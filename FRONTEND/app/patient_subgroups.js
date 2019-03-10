'use strict';

import { Diseases } from './diseases';
import { Genes } from './genes';
import { Drugs } from './drugs';

// Singleton variables
var _PatientSubgroups;
var _PatientSubgroupNodes;
var _PatientSubgroupNodesByDisease;

var _PatientSubgroupsHash;
var _PatientSubgroupsNodeHash;

const ENSEMBL_GENE_SEARCH='http://www.ensembl.org/Homo_sapiens/Location/View?g=';
const DRUGBANK_SEARCH='https://www.drugbank.ca/unearth/q?utf8=%E2%9C%93&searcher=drugs&query=';

function ensLink(g) {
	let saneG = encodeURIComponent(g);
	return '<a href="'+ENSEMBL_GENE_SEARCH + saneG + '" target="_blank">'+saneG+'</a>';
}

function drugbankLink(dr) {
	let saneD = encodeURIComponent(dr);
	return '<a href="'+DRUGBANK_SEARCH + saneD + '" target="_blank">'+saneD+'</a>';
}

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
					_PatientSubgroupNodesByDisease = {};
					_PatientSubgroupNodes = _PatientSubgroups.map(function(psg) {
						// jshint camelcase: false 
						let name = 'Sub '+psg.name.split('.')[1]+'\n('+psg.size+')';
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
						
						let retval = {
							classes: 'PSG',
							data: retpsg
						};
						
						if(psg.disease_id in _PatientSubgroupNodesByDisease) {
							_PatientSubgroupNodesByDisease[psg.disease_id].push(retval);
						} else {
							_PatientSubgroupNodesByDisease[psg.disease_id] = [ retval ];
						}
						
						return retval;
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
						classes: 'CM CM'+((retpsgc.rel_risk > 0) ? 'p' : 'n')
					};
				});
				
				this.network = null;
				
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
				
				if(dPSDI instanceof Array) {
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
				}
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
				
				if(dPSGI instanceof Array) {
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
				}
			})
		);
		
		return fetchPromises;
	}
	
	getAbsRelRiskRange() {
		return this.absRelRiskRange;
	}
	
	// getCYComorbiditiesNetwork
	getFetchedNetwork() {
		// jshint camelcase: false
		// Fixups from diseases
		
		if(this.network === null) {
			//let diseaseNodes = this.diseases.getDiseaseNodes();
			let setDiseaseIds = new Set(this.diseaseIds);
			let selectedDiseases = this.selectedDiseases = this.diseases.getDiseaseNodes().filter((d) => setDiseaseIds.has(d.data.disease_id));
			
			let dPSGIHash = this.diseasePatientSubgroupGeneIntersectHash;
			let dPSDIHash = this.diseasePatientSubgroupDrugIntersectHash;
			
			let drugsHash = {};
			
			this.drugs.getDrugs().forEach((dr) => {
				drugsHash[dr.id] = dr;
			});
			
			// The patient subgroups related to the selected diseases
			this.minClusterSize = +Infinity;
			this.maxClusterSize = -Infinity;
			let initialMinSelfClusterSize = Infinity;
			let selectedPatientSubgroupNodes = Array.from(setDiseaseIds).filter((disease_id) => {
				return disease_id in _PatientSubgroupNodesByDisease;
			}).map((disease_id) => {
				let localSubgroup = _PatientSubgroupNodesByDisease[disease_id];
				
				// The biggest subgroup from this disease
				let initialSelfClusterSize = -Infinity;
				// update min / max cluster size
				localSubgroup.forEach((psg) => {
					if(psg.data.size > this.maxClusterSize) {
						this.maxClusterSize = psg.data.size;
					}
					
					if(psg.data.size < this.minClusterSize) {
						this.minClusterSize = psg.data.size;
					}
					
					if(psg.data.size > initialSelfClusterSize) {
						initialSelfClusterSize = psg.data.size;
					}
				});
				
				// The biggest subgroup from each disease, but
				// the least from the other ones
				if(initialSelfClusterSize < initialMinSelfClusterSize) {
					initialMinSelfClusterSize = initialSelfClusterSize;
				}
				
				return localSubgroup;
			}).reduce((acc, val) => acc.concat(val), []);
			
			//console.log("GSize",selectedDiseases.map((dn) => {
			//	return (dn.data.disease_id in _PatientSubgroupNodesByDisease) ? _PatientSubgroupNodesByDisease[dn.data.disease_id].length : -1;
			//}));
			// This code is needed to update the subtotals
			selectedDiseases.forEach((dn) => {
				if(dn.data.disease_id in _PatientSubgroupNodesByDisease) {
					let data = dn.data;
					
					// up propagation
					if(!('_propUp' in data)) {
						// Propagating the number of patient subgroups related to the disease
						data.childcount = _PatientSubgroupNodesByDisease[data.disease_id].length;
						
						// Setting up the groupname
						data.groupname = data.name+ '\n(' + data.childcount + ' subgroup' + ((data.childcount !== 1) ? 's' : '') + ')';
						data._propUp = true;
					}
					
					// down propagation
					_PatientSubgroupNodesByDisease[data.disease_id].forEach((psn) => {
						psn.data.disease_name = data.name;
						psn.data.color = data.color;
						
						// Some stats propagation
						if(psn.data.patient_subgroup_id in dPSDIHash) {
							let upArr = [];
							dPSDIHash[psn.data.patient_subgroup_id].upSet.forEach((drug_id) => upArr.push(drugsHash[drug_id].name));
							let downArr = [];
							dPSDIHash[psn.data.patient_subgroup_id].downSet.forEach((drug_id) => downArr.push(drugsHash[drug_id].name));
							psn.data.drugs = {
								up: upArr,
								down: downArr
							};
						} else {
							psn.data.drugs = {
								up: [],
								down: []
							};
						}
						
						if(psn.data.patient_subgroup_id in dPSGIHash) {
							psn.data.genes = {
								up: Array.from(dPSGIHash[psn.data.patient_subgroup_id].upSet),
								down: Array.from(dPSGIHash[psn.data.patient_subgroup_id].downSet)
							};
						} else {
							psn.data.genes = {
								up: [],
								down: []
							};
						}
					});
				}
			});
			
			// Labelling intra-disease commorbidities
			// Getting minimum and maximum cluster sizes
			let minAbsRisk = Infinity;
			let maxAbsRisk = -Infinity;
			
			// Intercluster
			let initialMinClusterSize = Infinity;
			
			// Inter disease
			let diseasePairMaxAbsRelRisk = {};
			// Intra disease
			let diseaseSelfMaxAbsRelRisk = {};
			
			
			let selectedDiseasesHash = {};
			selectedDiseases.forEach((d) => {
				selectedDiseasesHash[d.data.disease_id] = d.data;
			});
			
			this.patientSubgroupComorbidityNetworkEdges.forEach((edge) => {
				let fromPSG = _PatientSubgroupsHash[edge.data.from_id];
				let toPSG = _PatientSubgroupsHash[edge.data.to_id];
				
				// Labelling intra-disease commorbidities
				edge.data.isIntraDisease = fromPSG.disease_id === toPSG.disease_id;
				
				// Getting the minimum and maximum absolute risk
				if(minAbsRisk > edge.data.abs_rel_risk) {
					minAbsRisk = edge.data.abs_rel_risk;
				}
				
				if(maxAbsRisk < edge.data.abs_rel_risk) {
					maxAbsRisk = edge.data.abs_rel_risk;
				}
				
				let selectedEdgeHash;
				if(edge.data.isIntraDisease) {
					selectedEdgeHash = diseaseSelfMaxAbsRelRisk;
				} else {
					selectedEdgeHash = diseasePairMaxAbsRelRisk;
				}
				
				// Identifying the initial cutoff, which allows viewing at least one arc from each node
				let a;
				let b;
				if(fromPSG.disease_id < toPSG.disease_id) {
					a = fromPSG;
					b = toPSG;
				} else {
					b = fromPSG;
					a = toPSG;
				}
				
				let edgeDisId =  a.disease_id + '_' + b.disease_id;
				if(!(edgeDisId in selectedEdgeHash) || (edge.data.abs_rel_risk > selectedEdgeHash[edgeDisId])) {
					selectedEdgeHash[edgeDisId] = edge.data.abs_rel_risk;
					
					if(!edge.data.isIntraDisease) {
						// Identifying the initial cluster size, which allows viewing at least each related disease with clusters
						if(initialMinClusterSize > edge.data.from_size) {
							initialMinClusterSize = edge.data.from_size;
						}
						
						if(initialMinClusterSize > edge.data.to_size) {
							initialMinClusterSize = edge.data.to_size;
						}
					}
				}
				
				// Adding some edge stats
				if(edge.data.rel_risk > 0) {
					if((edge.data.from_id in dPSDIHash) && (edge.data.to_id in dPSDIHash)) {
						let fromDrugSets = dPSDIHash[edge.data.from_id];
						let toDrugSets = dPSDIHash[edge.data.to_id];
						
						let upArr = [];
						fromDrugSets.upSet.intersection(toDrugSets.upSet).forEach((drug_id) => upArr.push(drugsHash[drug_id].name));
						let downArr = [];
						fromDrugSets.downSet.intersection(toDrugSets.downSet).forEach((drug_id) => downArr.push(drugsHash[drug_id].name));
						
						edge.data.drugs = {
							up: upArr,
							down: downArr
						};
					} else {
						edge.data.drugs = {
							up: [],
							down: []
						};
					}
					
					if(edge.data.from_id in dPSGIHash && edge.data.to_id in dPSGIHash) {
						let fromGeneSets = dPSGIHash[edge.data.from_id];
						let toGeneSets = dPSGIHash[edge.data.to_id];
						
						edge.data.genes = {
							up: Array.from(fromGeneSets.upSet.intersection(toGeneSets.upSet)),
							down: Array.from(fromGeneSets.downSet.intersection(toGeneSets.downSet))
						};
					} else {
						edge.data.genes = {
							up: [],
							down: []
						};
					}
				} else {
					if((edge.data.from_id in dPSDIHash) && (edge.data.to_id in dPSDIHash)) {
						let fromDrugSets = dPSDIHash[edge.data.from_id];
						let toDrugSets = dPSDIHash[edge.data.to_id];
						
						let upArr = [];
						fromDrugSets.upSet.intersection(toDrugSets.downSet).forEach((drug_id) => upArr.push(drugsHash[drug_id].name));
						let downArr = [];
						fromDrugSets.downSet.intersection(toDrugSets.upSet).forEach((drug_id) => downArr.push(drugsHash[drug_id].name));
						
						edge.data.drugs = {
							up: upArr,
							down: downArr
						};
					} else {
						edge.data.drugs = {
							up: [],
							down: []
						};
					}
					
					if(edge.data.from_id in dPSGIHash && edge.data.to_id in dPSGIHash) {
						let fromGeneSets = dPSGIHash[edge.data.from_id];
						let toGeneSets = dPSGIHash[edge.data.to_id];
						
						edge.data.genes = {
							up: Array.from(fromGeneSets.upSet.intersection(toGeneSets.downSet)),
							down: Array.from(fromGeneSets.downSet.intersection(toGeneSets.upSet))
						};
					} else {
						edge.data.genes = {
							up: [],
							down: []
						};
					}
				}
			});
			
			// Getting the minimum arc from the max arcs
			let initialAbsCutoff = Infinity;
			for(let pair in diseasePairMaxAbsRelRisk) {
				if(initialAbsCutoff > diseasePairMaxAbsRelRisk[pair]) {
					initialAbsCutoff = diseasePairMaxAbsRelRisk[pair];
				}
			}
			
			// Switch to the intra case
			if(initialAbsCutoff > maxAbsRisk) {
				for(let pair in diseaseSelfMaxAbsRelRisk) {
					if(initialAbsCutoff > diseaseSelfMaxAbsRelRisk[pair]) {
						initialAbsCutoff = diseaseSelfMaxAbsRelRisk[pair];
					}
				}
			}
			
			// Giving a saner initial version to the minClusterSize
			if(initialMinClusterSize < Infinity) {
				this.initialMinClusterSize = initialMinClusterSize;
			} else if(initialMinSelfClusterSize < Infinity) {
				this.initialMinClusterSize = initialMinSelfClusterSize;
			}
			
			// Saving the range and cutoff for later processing
			this.absRelRiskRange = {
				min: minAbsRisk,
				initial: initialAbsCutoff,
				max: maxAbsRisk
			};
			
			let setDiseaseGroupIds = new Set(selectedDiseases.map((d) => d.data.disease_group_id));
			let selectedDiseaseGroups = this.diseases.getDiseaseGroupNodes().filter((dg) => setDiseaseGroupIds.has(dg.data.disease_group_id));
			
			this.network = {
				nodes: [
					...selectedPatientSubgroupNodes,
					...selectedDiseases,
					...selectedDiseaseGroups
				],
				edges: this.patientSubgroupComorbidityNetworkEdges
			};
		}
		
		return this.network;
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
		this.params.title = 'Patient subgroups from <span style="font-weight: bold;" title="'+this.selectedDiseases.map((d) => d.data.name).join('\n')+'">'+this.selectedDiseases.length+'</span> diseases';
		
		return this.params;
	}
	
	// Controls and their associated filters
	getControlsSetup() {
		let absRelRiskData = this.getAbsRelRiskRange();
		let initialAbsRelRiskVal = Math.floor(absRelRiskData.initial*10)/10;	
		
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
				label: 'Hide intra-disease edges',
				param: 'hideInternalEdgesVal',
				fn: () => this.cmBrowser.batch(() => this.cmBrowser.filterOnConditions())
			},
			{
				filter: 'edges',
				attr: 'drugs',
				filterfn:  function(attrVal,paramVal) { return paramVal && attrVal.up.length === 0 && attrVal.down.length === 0; },
				filterOnCtx: false,
				type: 'checkbox',
				label: 'Hide edges without common/inverse drugs',
				param: 'hideDruglessEdgesVal',
				fn: () => this.cmBrowser.batch(() => this.cmBrowser.filterOnConditions())
			},
			{
				filter: 'edges',
				attr: 'genes',
				filterfn:  function(attrVal,paramVal) { return paramVal && attrVal.up.length === 0 && attrVal.down.length === 0; },
				filterOnCtx: false,
				type: 'checkbox',
				label: 'Hide edges without common/inverse genes',
				param: 'hideGenelessEdgesVal',
				fn: () => this.cmBrowser.batch(() => this.cmBrowser.filterOnConditions())
			},
			{
				type: 'button-group',
			},
			//{
			//	type: 'button',
			//	label: '<i class="far fa-object-group"></i>',
			//	layoutOpts: {
			//		randomize: true
			//	},
			//	fn: () => this.toggleDiseaseGroups()
			//},
			//{
			//	type: 'button',
			//	label: '<i class="far fa-object-ungroup"></i>',
			//	layoutOpts: {
			//		randomize: true
			//	},
			//	fn: () => this.toggleDiseaseGroups()
			//},
			{
				type: 'button',
				label: '<i class="fas fa-random"></i>',
				layoutOpts: {
					randomize: true,
					flow: null
				}
			},
			{
				type: 'button',
				label: '<i class="fas fa-long-arrow-alt-down"></i>',
				layoutOpts: {
					flow: {
						axis: 'y',
						minSeparation: 30
					}
				}
			},
			{
				type: 'legend',
				// Reuse legend from diseases
				domNode: this.diseases.getLegendDOM()
			}
		];
		
		return controlsDesc;
	}
	
	getNextViewSetup() {
		// No next view right now
		return null;
	}
	
	makeNodeTooltipContent(node) {
		if(node.classNames().indexOf('D') !== -1) {
			return this.diseases.makeNodeTooltipContent(node);
		}
		
		let patientSubgroupName = node.data('disease_name') + ' ' + node.data('name');
		
		let content = document.createElement('div');
		content.setAttribute('style','font-size: 1.3em;');
		
		//content.innerHTML = 'Tippy content';
		let cInner = '<b>'+patientSubgroupName+'</b>'+
			'<div style="text-align: left;">' +
			'Number of patients: ' + node.data('size')
		;
		try {
			cInner += '<br/>' +
				'Drugs: ' +
				'<div class="updown">'+
					'<div>'+
						'<i class="fas fa-sort-up" aria-hidden="true"></i> ' + node.data('drugs').up.length +
						'<div class="scrollblock">'+node.data('drugs').up.map(drugbankLink).join('<br/>')+'</div>' +
					'</div>'+
					'<div>'+
						' <i class="fas fa-sort-down" aria-hidden="true"></i> ' + node.data('drugs').down.length + '<br/>' +
						'<div class="scrollblock">'+node.data('drugs').down.map(drugbankLink).join('<br/>')+'</div>' +
					'</div>'+
				'</div>'+
				'Genes: '+
				'<div class="updown">'+
					'<div>'+
						'<i class="fas fa-sort-up" aria-hidden="true"></i> ' + node.data('genes').up.length +
						'<div class="scrollblock">'+node.data('genes').up.map(ensLink).join('<br/>')+'</div>' +
					'</div>'+
					'<div>'+
						' <i class="fas fa-sort-down" aria-hidden="true"></i> ' + node.data('genes').down.length +
						'<div class="scrollblock">'+node.data('genes').down.map(ensLink).join('<br/>')+'</div>'+
					'</div>'+
				'</div>';
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
		
		if(edge.data('rel_risk') > 0) {
			content.innerHTML = '<b><u>Relative risk</u></b>: ' + edge.data('rel_risk') +
				'<div><b>Source</b>: '+source.data('label') + '<br />\n' +
				'<b>Target</b>: '+target.data('label')+'<br />\n'+
				'<b>Common drugs</b>: '+
				'<div class="updown">'+
					'<div>'+
						'<i class="fas fa-angle-double-up" aria-hidden="true" title="Up both in source and target"></i> ' + edge.data('drugs').up.length +
						'<div class="scrollblock">'+edge.data('drugs').up.map(drugbankLink).join('<br/>')+'</div>' +
					'</div>'+
					'<div>'+
						' <i class="fas fa-angle-double-down" aria-hidden="true" title="Down both in source and target"></i> ' + edge.data('drugs').down.length + '<br/>' +
						'<div class="scrollblock">'+edge.data('drugs').down.map(drugbankLink).join('<br/>')+'</div>' +
					'</div>'+
				'</div>'+
				'<b>Common genes</b>: '+
				'<div class="updown">'+
					'<div>'+
						'<i class="fas fa-angle-double-up" aria-hidden="true" title="Up both in source and target"></i> ' + edge.data('genes').up.length +
						'<div class="scrollblock">'+edge.data('genes').up.map(ensLink).join('<br/>')+'</div>' +
					'</div>'+
					'<div>'+
						' <i class="fas fa-angle-double-down" aria-hidden="true" title="Down both in source and target"></i> ' + edge.data('genes').down.length +
						'<div class="scrollblock">'+edge.data('genes').down.map(ensLink).join('<br/>')+'</div>' +
					'</div>'+
				'</div>';
		} else {
			content.innerHTML = '<b><u>Relative risk</u></b>: ' + edge.data('rel_risk') +
				'<div><b>Source</b>: '+source.data('label') + '<br />\n' +
				'<b>Target</b>: '+target.data('label')+'<br />\n'+
				'<b>Inverse drugs</b>: '+
				'<div class="updown">'+
					'<div>'+
						'<i class="fas fa-random" aria-hidden="true" title="Up in source, down in target"></i> ' + edge.data('drugs').up.length +
						'<div class="scrollblock">'+edge.data('drugs').up.map(drugbankLink).join('<br/>')+'</div>' +
					'</div>'+
					'<div>'+
						' <i class="fas fa-random fa-rotate-180" aria-hidden="true" title="Down in source, up in target"></i> ' + edge.data('drugs').down.length + '<br/>' +
						'<div class="scrollblock">'+edge.data('drugs').down.map(drugbankLink).join('<br/>')+'</div>' +
					'</div>'+
				'</div>'+
				'<b>Inverse genes</b>: '+
				'<div class="updown">'+
					'<div>'+
						'<i class="fas fa-random" aria-hidden="true" title="Up in source, down in target"></i> ' + edge.data('genes').up.length +
						'<div class="scrollblock">'+edge.data('genes').up.map(ensLink).join('<br/>')+'</div>' +
					'</div>'+
					'<div>'+
						' <i class="fas fa-random fa-rotate-180" aria-hidden="true" title="Down in source, up in target"></i> ' + edge.data('genes').down.length +
						'<div class="scrollblock">'+edge.data('genes').down.map(ensLink).join('<br/>')+'</div>' +
					'</div>'+
				'</div>';
		}
		return content;
	}
}
