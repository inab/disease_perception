'use strict';

import { Diseases } from './diseases';

// Singleton variables
var _PatientSubgroups;
var _PatientSubgroupNodes;
var _PendingColorPropagation = true;

var _PatientSubgroupsHash;
var _PatientSubgroupsNodeHash;

function distinctFilter(value,index,self) {
	return index === 0 || self.lastIndexOf(value,index-1) < 0;
}

export class PatientSubgroups {
	constructor(cmBrowser) {
		this.cmBrowser = cmBrowser;
		this.diseases = new Diseases(cmBrowser);
	}
	
	// This method returns an array of promises, ready to be run in parallel
	fetch(diseaseIds,minClusterSize=4) {
		let fetchPromises = this.diseases.fetch();
		
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
		
		let commaDiseaseIds = diseaseIds.join(',');
		
		fetchPromises.push(
			//fetch('api/diseases/ps_comorbidities/'+encodeURIComponent(commaDiseaseIds)+'/min_size/'+minClusterSize, {mode: 'no-cors'})
			fetch('api/diseases/ps_comorbidities/'+encodeURIComponent(commaDiseaseIds), {mode: 'no-cors'})
			.then(function(res) {
				return res.json();
			})
			.then((decodedJson) => {
				// jshint camelcase: false
				this.diseaseIds = [ ...diseaseIds ];
				this.initialMinClusterSize = minClusterSize;
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
						data: retpsgc
					};
				});
				this.pendingIntraDiseaseCheck = true;
				
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
		if(_PendingColorPropagation) {
			let diseaseColorsHash = {};
			
			diseaseNodes.forEach((dn) => {
				diseaseColorsHash[dn.data.disease_id] = dn.data.color;
			});
			_PatientSubgroupNodes.forEach((psn) => {
				psn.data.color = diseaseColorsHash[psn.data.disease_id];
			});
			
			_PendingColorPropagation = false;
		}
		
		// Labelling intra-disease commorbidities
		// Getting minimum and maximum cluster sizes
		if(this.pendingIntraDiseaseCheck) {
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
			});
			this.pendingIntraDiseaseCheck = false;
		}
		
		let setDiseaseIds = new Set(this.diseaseIds);
		let selectedDiseases = diseaseNodes.filter((d) => setDiseaseIds.has(d.data.disease_id));
		let setDiseaseGroupIds = new Set(selectedDiseases.map((d) => d.data.disease_group_id));
		let selectedDiseaseGroups = this.diseases.getDiseaseGroupNodes().filter((dg) => setDiseaseGroupIds.has(dg.data.disease_group_id));
		
		return {
			nodes: [
				// jshint ignore:start
				..._PatientSubgroupNodes,
				...selectedDiseases,
				...selectedDiseaseGroups
				// jshint ignore:end
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
			{
				type: 'slider',
				label: 'Node spacing',
				param: 'nodeSpacing',
				min: 1,
				max: 50,
				// Specific from cola algorithm
				initial: 5
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
		content.innerHTML = '<b>'+patientSubgroupName+'</b>'+
			'<div style="text-align: left;">' +
			'Number of patients: ' + node.data('size') +
			'</div>';
		

		return content;
	}
	
	makeEdgeTooltipContent(edge) {
		let content = document.createElement('div');
		content.setAttribute('style','font-size: 1.3em;text-align: left;');
		
		let source = edge.source();
		let target = edge.target();
		
		
		content.innerHTML = '<b><u>Relative risk</u></b>: ' + edge.data('rel_risk') +
			'<div><b>Source</b>: '+source.data('label') + '<br />\n' +
			'<b>Target</b>: '+target.data('label')+'</div>';
		return content;
	}
}
