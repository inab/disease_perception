import { Diseases } from './diseases';

// Singleton variables
var _PatientSubgroups;
var _PatientSubgroupNodes;
var _PendingColorPropagation = true;

var _PatientSubgroupsNodeHash;

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
					_PatientSubgroupsNodeHash = {};
					_PatientSubgroupNodes = _PatientSubgroups.map(function(psg) {
						// jshint camelcase: false 
						let retpsg = {
							color: '#008020',
							// jshint ignore:start
							...psg,
							// jshint ignore:end
							// Unique identifiers
							patient_subgroup_id: psg.id,
							id: 'PSG'+psg.id,
							parent: 'D'+psg.disease_id,
							classes: 'PSG'
						};
						_PatientSubgroupsNodeHash[psg.id] = retpsg;
						
						return {
							data: retpsg
						};
					});
					
					return _PatientSubgroups;
				})
			);
		}
		
		let commaDiseaseIds = diseaseIds.join(',');
		
		fetchPromises.push(
			fetch('api/diseases/ps_comorbidities/'+encodeURIComponent(commaDiseaseIds)+'/min_size/'+minClusterSize, {mode: 'no-cors'})
			.then(function(res) {
				return res.json();
			})
			.then((decodedJson) => {
				this.diseaseIds = [ ...diseaseIds ];
				let dPSCN = this.diseasePatientSubgroupComorbidityNetwork = decodedJson;
				
				this.patientSubgroupComorbidityNetworkEdges = dPSCN.map(function(psgc,psgci) {
					// Will be used later
					// jshint camelcase: false 
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
					delete retpsgc.from_id;
					delete retpsgc.to_id;
					
					return {
						data: retpsgc
					};
				});
				
				let minAbsRisk = Infinity;
				let maxAbsRisk = -Infinity;
				let initialAbsCutoff = -Infinity;
				if(dPSCN.length > 0) {
					let dPSCNe = [...dPSCN];
					
					// jshint camelcase: false
					dPSCNe.sort(function(e1,e2) { return e1.abs_rel_risk - e2.abs_rel_risk; });
					minAbsRisk = dPSCNe[0].abs_rel_risk;
					maxAbsRisk = dPSCNe[dPSCNe.length - 1].abs_rel_risk;
					
					// Selecting the initial absolute cutoff risk, based on the then biggest values
					initialAbsCutoff = dPSCNe[Math.floor(dPSCNe.length * 0.95)].abs_rel_risk;
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
			let absRelRiskData = this.getAbsRelRiskRange();
			
			this.params = {
				name: 'cola',
				absRelRiskVal: absRelRiskData.initial,
				// Specific from cola algorithm
				nodeSpacing: 5,
				edgeLengthVal: 45,
				animate: true,
				randomize: false,
				maxSimulationTime: 1500
			};
		}
		
		return this.params;
	}
	
	makeNodeTooltipContent(node) {
		let patientSubgroupName = node.data('name');
		
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
			'<div><b>Source</b>: '+source.data('name') + '<br />\n' +
			'<b>Target</b>: '+target.data('name')+'</div>';
		return content;
	}
}
