'use strict';

import { Diseases } from './diseases';
import { Genes } from './genes';
import { Drugs } from './drugs';

// Singleton variables
var _PatientSubgroups;
var _PatientSubgroupNodes;
var _PendingNodePropagation = true;

var _PatientSubgroupsHash;
var _PatientSubgroupsNodeHash;

// Adding useful method
Set.prototype.intersection = function(setB) {
	let intersection = new Set();
	setB.forEach((elem) => {
		if(this.has(elem)) {
			intersection.add(elem);
		}
	});
	
	return intersection;
};

function distinctFilter(value,index,self) {
	return index === 0 || self.lastIndexOf(value,index-1) < 0;
}

export class PatientSubgroups {
	constructor(cmBrowser) {
		this.cmBrowser = cmBrowser;
		this.diseases = new Diseases(cmBrowser);
		this.genes = new Genes(cmBrowser);
		this.drugs = new Drugs(cmBrowser);
	}
	
	// This method returns an array of promises, ready to be run in parallel
	fetch(diseaseIds,minClusterSize=4) {
		let fetchPromises = [].concat(this.diseases.fetch(),this.genes.fetch(),this.drugs.fetch());
		
		if(_PatientSubgroups===undefined) {
			fetchPromises.push(
				fetch('api/patients/subgroups', {mode: 'no-cors'})
				.then(function(res) {
					return res.json();
				})
				.then(function(decodedJson) {
					_PatientSubgroups = decodedJson;
					_PatientSubgroupsHash = {};
					_PatientSubgroupsNodeHash = {};
					_PatientSubgroupNodes = _PatientSubgroups.map(function(psg) {
						// jshint camelcase: false 
						let name = 'Subgroup\n'+psg.name.split('.')[1];
						let retpsg = {
							color: '#008020',
							// jshint ignore:start
							...psg,
							// jshint ignore:end
							name: name,
							label: psg.name,
							// Unique identifiers
							patient_subgroup_id: psg.id,
							id: 'PSG'+psg.id,
							parent: 'D'+psg.disease_id
						};
						_PatientSubgroupsHash[psg.id] = retpsg;
						_PatientSubgroupsNodeHash[retpsg.id] = retpsg;
						
						return {
							classes: 'PSG',
							data: retpsg
						};
					});
					
					return _PatientSubgroups;
				})
			);
		}
		
		this.diseaseIds = [ ...diseaseIds ];
		this.initialMinClusterSize = minClusterSize;
		let commaDiseaseIds = diseaseIds.join(',');
		
		fetchPromises.push(
			//fetch('api/diseases/'+encodeURIComponent(commaDiseaseIds)+'/patients/subgroups/comorbidities/min_size/'+minClusterSize, {mode: 'no-cors'})
			fetch('api/diseases/'+encodeURIComponent(commaDiseaseIds)+'/patients/subgroups/comorbidities', {mode: 'no-cors'})
			.then(function(res) {
				return res.json();
			})
			.then((decodedJson) => {
				// jshint camelcase: false
				let dPSCN = this.diseasePatientSubgroupComorbidityNetwork = decodedJson;
				
				this.patientSubgroupComorbidityNetworkEdges = dPSCN.map(function(psgc,psgci) {
					// Will be used later
					psgc.abs_rel_risk = Math.abs(psgc.rel_risk);
					// Preparation
					let retpsgc = {
						// jshint ignore:start
						...psgc,
						// jshint ignore:end
						// Unique identifiers
						id: 'PSGC'+psgci,
						source: 'PSG'+psgc.from_id,
						target: 'PSG'+psgc.to_id
					};
					//delete retpsgc.from_id;
					//delete retpsgc.to_id;
					
					return {
						data: retpsgc,
						classes: 'CM'
					};
				});
				this.pendingEdgeStats = true;
				
				let minAbsRisk = Infinity;
				let maxAbsRisk = -Infinity;
				let initialAbsCutoff = -Infinity;
				if(dPSCN.length > 0) {
					let dPSCNe = dPSCN.map((e) => e.abs_rel_risk);
					
					dPSCNe.sort(function(e1,e2) { return e1 - e2; });
					dPSCNe = dPSCNe.filter(distinctFilter);
					minAbsRisk = dPSCNe[0];
					maxAbsRisk = dPSCNe[dPSCNe.length - 1];
					
					// Selecting the initial absolute cutoff risk, based on the then biggest values
					initialAbsCutoff = dPSCNe[Math.floor(dPSCNe.length * 0.5)];
				}
				
				// Saving the range and cutoff for later processing
				this.absRelRiskRange = {
					min: minAbsRisk,
					initial: initialAbsCutoff,
					max: maxAbsRisk
				};
				
				return decodedJson;
			})
		);
		
		fetchPromises.push(
			fetch('api/diseases/'+encodeURIComponent(commaDiseaseIds)+'/patients/subgroups/drugs', {mode: 'no-cors'})
			.then(function(res) {
				return res.json();
			})
			.then((decodedJson) => {
				// jshint camelcase: false
				let dPSDI = this.diseasePatientSubgroupDrugIntersect = decodedJson;
				let dPSDIE = this.diseasePatientSubgroupDrugIntersectEdges = [];
				
				let dPSDIHash = this.diseasePatientSubgroupDrugIntersectHash = {};
				
				dPSDI.forEach(function(psd,psdi) {
					dPSDIHash[psd.patient_subgroup_id] = psd;
					let upList = [];
					let downList = [];
					psd.drugs.forEach(function(psde,psdei) {
						if(psde.regulation_sign > 0) {
							upList.push(psde.drug_id);
						} else {
							downList.push(psde.drug_id);
						}
						let retpsd = {
							// Unique identifiers
							id: 'PSDC'+psdi+'_'+psdei,
							source: 'Dr'+psde.drug_id,
							target: 'PSD'+psd.patient_subgroup_id,
							sign: psde.regulation_sign
						};
						
						dPSDIE.push({
							data: retpsd,
							classes: 'DI'
						});
					});
					psd.upSet = new Set(upList);
					psd.downSet = new Set(downList);
				});
			})
		);
		
		fetchPromises.push(
			fetch('api/diseases/'+encodeURIComponent(commaDiseaseIds)+'/patients/subgroups/genes', {mode: 'no-cors'})
			.then(function(res) {
				return res.json();
			})
			.then((decodedJson) => {
				// jshint camelcase: false
				let dPSGI = this.diseasePatientSubgroupGeneIntersect = decodedJson;
				let dPSGIE = this.diseasePatientSubgroupGeneIntersectEdges = [];
				
				let dPSGIHash = this.diseasePatientSubgroupGeneIntersectHash = {};
				
				dPSGI.forEach(function(psg,psgi) {
					dPSGIHash[psg.patient_subgroup_id] = psg;
					let upList = [];
					let downList = [];
					psg.genes.forEach(function(psge,psgei) {
						if(psge.regulation_sign > 0) {
							upList.push(psge.gene_symbol);
						} else {
							downList.push(psge.gene_symbol);
						}
						let retpsg = {
							// Unique identifiers
							id: 'PSGC'+psgi+'_'+psgei,
							source: psge.gene_symbol,
							target: 'PSD'+psg.patient_subgroup_id,
							sign: psge.regulation_sign
						};
						
						dPSGIE.push({
							data: retpsg,
							classes: 'GI'
						});
					});
					psg.upSet = new Set(upList);
					psg.downSet = new Set(downList);
				});
			})
		);
		
		return fetchPromises;
	}
	
	getAbsRelRiskRange() {
		return this.absRelRiskRange;
	}
	
	// getCYComorbiditiesNetwork
	getFetchedNetwork() {
		// Fixups from diseases
		// jshint camelcase: false
		let diseaseNodes = this.diseases.getDiseaseNodes();
			
		let dPSGIHash = this.diseasePatientSubgroupGeneIntersectHash;
		let dPSDIHash = this.diseasePatientSubgroupDrugIntersectHash;
		
		if(_PendingNodePropagation) {
			let diseaseColorsHash = {};
			
			diseaseNodes.forEach((dn) => {
				diseaseColorsHash[dn.data.disease_id] = dn.data.color;
			});
			_PatientSubgroupNodes.forEach((psn) => {
				psn.data.color = diseaseColorsHash[psn.data.disease_id];
				
				// Some stats propagation
				if(psn.data.patient_subgroup_id in dPSDIHash) {
					psn.data.drugsUp = Array.from(dPSDIHash[psn.data.patient_subgroup_id].upSet);
					psn.data.drugsDown = Array.from(dPSDIHash[psn.data.patient_subgroup_id].downSet);
				} else {
					psn.data.drugsUp = [];
					psn.data.drugsDown = [];
				}
				
				if(psn.data.patient_subgroup_id in dPSGIHash) {
					psn.data.genesUp = Array.from(dPSGIHash[psn.data.patient_subgroup_id].upSet);
					psn.data.genesDown = Array.from(dPSGIHash[psn.data.patient_subgroup_id].downSet);
				} else {
					psn.data.genesUp = [];
					psn.data.genesDown = [];
				}
			});
			
			_PendingNodePropagation = false;
		}
		
		// Labelling intra-disease commorbidities
		// Getting minimum and maximum cluster sizes
		if(this.pendingEdgeStats) {
			this.minClusterSize = +Infinity;
			this.maxClusterSize = -Infinity;
			
			this.patientSubgroupComorbidityNetworkEdges.forEach((edge) => {
				let fromPSG = _PatientSubgroupsHash[edge.data.from_id];
				let toPSG = _PatientSubgroupsHash[edge.data.to_id];
				
				// Getting minimum and maximum cluster sizes
				if(fromPSG.size > this.maxClusterSize) {
					this.maxClusterSize = fromPSG.size;
				}
				
				if(toPSG.size > this.maxClusterSize) {
					this.maxClusterSize = toPSG.size;
				}
				
				if(fromPSG.size < this.minClusterSize) {
					this.minClusterSize = fromPSG.size;
				}
				
				if(toPSG.size < this.minClusterSize) {
					this.minClusterSize = toPSG.size;
				}
				
				// Labelling intra-disease commorbidities
				edge.data.isIntraDisease = fromPSG.disease_id === toPSG.disease_id;
				
				// Adding some edge stats
				if((edge.data.from_id in dPSDIHash) && (edge.data.to_id in dPSDIHash)) {
					let fromDrugSets = dPSDIHash[edge.data.from_id];
					let toDrugSets = dPSDIHash[edge.data.to_id];
					
					edge.data.drugsUp = Array.from(fromDrugSets.upSet.intersection(toDrugSets.upSet));
					edge.data.drugsDown = Array.from(fromDrugSets.downSet.intersection(toDrugSets.downSet));
				} else {
					edge.data.drugsUp = [];
					edge.data.drugsDown = [];
				}
				
				if(edge.data.from_id in dPSGIHash && edge.data.to_id in dPSGIHash) {
					let fromGeneSets = dPSGIHash[edge.data.from_id];
					let toGeneSets = dPSGIHash[edge.data.to_id];
					
					edge.data.genesUp = Array.from(fromGeneSets.upSet.intersection(toGeneSets.upSet));
					edge.data.genesDown = Array.from(fromGeneSets.downSet.intersection(toGeneSets.downSet));
				} else {
					edge.data.genesUp = [];
					edge.data.genesDown = [];
				}
			});
			this.pendingEdgeStats = false;
		}
		
		let setDiseaseIds = new Set(this.diseaseIds);
		let selectedDiseases = diseaseNodes.filter((d) => setDiseaseIds.has(d.data.disease_id));
		let setDiseaseGroupIds = new Set(selectedDiseases.map((d) => d.data.disease_group_id));
		let selectedDiseaseGroups = this.diseases.getDiseaseGroupNodes().filter((dg) => setDiseaseGroupIds.has(dg.data.disease_group_id));
		
		return {
			nodes: [
				..._PatientSubgroupNodes,
				...selectedDiseases,
				...selectedDiseaseGroups
			],
			edges: this.patientSubgroupComorbidityNetworkEdges
		};
	}
	
	getGraphSetup() {
		if(this.params===undefined) {
			this.params = {
				name: 'cose-bilkent',
				// Specific from cola algorithm
				edgeLengthVal: 45,
				animate: true,
				randomize: false,
				maxSimulationTime: 1500
			};
		}
		
		return this.params;
	}
	
	// Controls and their associated filters
	getControlsSetup() {
		let absRelRiskData = this.getAbsRelRiskRange();
		let initialAbsRelRiskVal = Math.round(absRelRiskData.initial);	
		
		let controlsDesc = [
			{
				filter: 'edges',
				attr: 'abs_rel_risk',
				filterfn:  function(attrVal,paramVal) { return attrVal < paramVal; },
				filterOnCtx: true,
				type: 'slider',
				label: 'Cut-off on |Relative risk|',
				param: 'absRelRiskVal',
				min: absRelRiskData.min,
				max: absRelRiskData.max,
				initial: initialAbsRelRiskVal,
				scale: 'logarithmic',
				step: 0.1,
				fn: () => this.cmBrowser.batch(() => this.cmBrowser.filterOnConditions())
			},
			{
				filter: 'nodes',
				attr: 'size',
				filterfn: function(attrVal,paramVal) { return attrVal < paramVal; },
				filterOnCtx: true,
				type: 'slider',
				label: 'Cut-off on cluster size',
				param: 'clusterSizeVal',
				min: this.minClusterSize,
				max: this.maxClusterSize,
				initial: this.initialMinClusterSize,
				scale: 'logarithmic',
				fn: () => this.cmBrowser.batch(() => this.cmBrowser.filterOnConditions())
			},
			//{
			//	type: 'slider',
			//	label: 'Edge length',
			//	param: 'edgeLengthVal',
			//	min: 1,
			//	max: 200,
			//	initial: 45,
			//},
			//{
			//	type: 'slider',
			//	label: 'Node spacing',
			//	param: 'nodeSpacing',
			//	min: 1,
			//	max: 50,
			//	// Specific from cola algorithm
			//	initial: 5
			//},
			{
				filter: 'edges',
				attr: 'isIntraDisease',
				filterfn:  function(attrVal,paramVal) { return paramVal && attrVal; },
				filterOnCtx: false,
				type: 'checkbox',
				label: 'Hide internal edges',
				param: 'hideInternalEdgesVal',
				fn: () => this.cmBrowser.batch(() => this.cmBrowser.filterOnConditions())
			},
			{
				type: 'button-group',
			},
			//{
			//	type: 'button',
			//	label: '<i class="fa fa-object-group"></i>',
			//	layoutOpts: {
			//		randomize: true
			//	},
			//	fn: () => this.toggleDiseaseGroups()
			//},
			//{
			//	type: 'button',
			//	label: '<i class="fa fa-object-ungroup"></i>',
			//	layoutOpts: {
			//		randomize: true
			//	},
			//	fn: () => this.toggleDiseaseGroups()
			//},
			{
				type: 'button',
				label: '<i class="fa fa-random"></i>',
				layoutOpts: {
					randomize: true,
					flow: null
				}
			},
			{
				type: 'button',
				label: '<i class="fa fa-long-arrow-down"></i>',
				layoutOpts: {
					flow: {
						axis: 'y',
						minSeparation: 30
					}
				}
			}
		];
		
		return controlsDesc;
	}
	
	getNextViewSetup() {
		// No next view right now
		return null;
	}
	
	makeNodeTooltipContent(node) {
		let patientSubgroupName = node.data('label');
		
		let content = document.createElement('div');
		content.setAttribute('style','font-size: 1.3em;');
		
		//content.innerHTML = 'Tippy content';
		let cInner = '<b>'+patientSubgroupName+'</b>'+
			'<div style="text-align: left;">' +
			'Number of patients: ' + node.data('size')
		;
		try {
			cInner += '<br/>' +
				'Drugs (+/-): ' + node.data('drugsUp').length + ' / ' + node.data('drugsDown').length + '<br/>' +
				'Genes (+/-): ' + node.data('genesUp').length + ' / ' + node.data('genesDown').length;
		} catch(e) {
			// DoNothing(R)
		}
		cInner += '</div>';
			
		content.innerHTML = cInner;

		return content;
	}
	
	makeEdgeTooltipContent(edge) {
		let content = document.createElement('div');
		content.setAttribute('style','font-size: 1.3em;text-align: left;');
		
		let source = edge.source();
		let target = edge.target();
		
		
		content.innerHTML = '<b><u>Relative risk</u></b>: ' + edge.data('rel_risk') +
			'<div><b>Source</b>: '+source.data('label') + '<br />\n' +
			'<b>Target</b>: '+target.data('label')+'<br />\n'+
			'<b>Common drugs (+/-)</b>: ' + edge.data('drugsUp').length + ' / ' + edge.data('drugsDown').length + '<br/>' +
			'<b>Common genes (+/-)</b>: ' + edge.data('genesUp').length + ' / ' + edge.data('genesDown').length +
			'</div>';
		return content;
	}
}
