// Singleton variables
var _Diseases;
var _DiseaseNodes;

var _DiseaseGroups;
var _DiseaseGroupNodes;

var _DiseaseComorbiditiesNetwork;

var _DiseaseComorbiditiesNetworkMinAbsRisk;
var _DiseaseComorbiditiesNetworkMaxAbsRisk;
var _DiseaseComorbiditiesNetworkInitialAbsCutoff;

var _DiseaseComorbiditiesNetworkEdges;

export class Diseases {
	constructor(cyContainer) {
		this.cyContainer = cyContainer;
	}
	
	// This method returns an array of promises, ready to be run in parallel
	fetch() {
		let fetchPromises = [];
		
		if(_Diseases===undefined) {
			// This is from the fetch API
			fetchPromises.push(
				fetch('api/diseases', {mode: 'no-cors'})
				.then(function(res) {
					return res.json();
				})
				.then(function(decodedJson) {
					_Diseases = decodedJson;
					_DiseaseNodes = _Diseases.map(function(dis) {
						let retdis = {
							// jshint ignore:start
							...dis
							// jshint ignore:end
						};
						// Unique identifiers
						retdis.id = 'D'+dis.id;
						// jshint camelcase: false 
						retdis.parent = 'DG'+dis.disease_group_id;
						delete retdis.disease_group_id;
						return {
							data: retdis
						};
					});
					return _Diseases;
				})
			);
		}
		
		if(_DiseaseGroups===undefined) {
			fetchPromises.push(
				fetch('api/diseases/groups', {mode: 'no-cors'})
				.then(function(res) {
					return res.json();
				})
				.then(function(decodedJson) {
					_DiseaseGroups = decodedJson;
					_DiseaseGroupNodes = _DiseaseGroups.map(function(dg) {
						let retdg = {
							// jshint ignore:start
							...dg
							// jshint ignore:end
						};
						// Unique identifiers
						retdg.id = 'DG'+dg.id;
						// jshint camelcase: false 
						return {
							data: retdg
						};
					});
					return _DiseaseGroups;
				})
			);
		}
		
		if(_DiseaseComorbiditiesNetwork===undefined) {
			fetchPromises.push(
				fetch('api/diseases/comorbidities', {mode: 'no-cors'})
				.then(function(res) {
					return res.json();
				})
				.then(function(decodedJson) {
					_DiseaseComorbiditiesNetwork = decodedJson;
					
					_DiseaseComorbiditiesNetworkEdges = _DiseaseComorbiditiesNetwork.map(function(dc,dci) {
						// Will be used later
						// jshint camelcase: false 
						dc.abs_rel_risk = Math.abs(dc.rel_risk);
						// Preparation
						let retdc = {
							// jshint ignore:start
							...dc
							// jshint ignore:end
						};
						// Unique identifiers
						retdc.id = 'DC'+dci;
						retdc.source = 'D'+dc.from_id;
						retdc.target = 'D'+dc.to_id;
						delete retdc.from_id;
						delete retdc.to_id;
						
						return {
							data: retdc
						};
					});
					
					let minAbsRisk = Infinity;
					let maxAbsRisk = -Infinity;
					let initialAbsCutoff = -Infinity;
					if(_DiseaseComorbiditiesNetwork.length > 0) {
						let dcme = [..._DiseaseComorbiditiesNetwork];
						
						// jshint camelcase: false 
						dcme.sort(function(e1,e2) { return e1.abs_rel_risk - e2.abs_rel_risk; });
						minAbsRisk = dcme[0].abs_rel_risk;
						maxAbsRisk = dcme[dcme.length - 1].abs_rel_risk;
						
						// Selecting the initial absolute cutoff risk, based on the then biggest values
						initialAbsCutoff = dcme[Math.floor(dcme.length * 9 / 10)].abs_rel_risk;
					}
					
					// Saving the range and cutoff for later processing
					_DiseaseComorbiditiesNetworkMinAbsRisk = minAbsRisk;
					_DiseaseComorbiditiesNetworkMaxAbsRisk = maxAbsRisk;
					_DiseaseComorbiditiesNetworkInitialAbsCutoff = initialAbsCutoff;
					
					return _DiseaseComorbiditiesNetwork;
				})
			);
		}
		
		return fetchPromises;
	}
	
	getDiseases() {
		return _Diseases;
	}
	
	getComorbiditiesNetwork() {
		return _DiseaseComorbiditiesNetwork;
	}
	
	getAbsRelRiskRange() {
		return {
			min: _DiseaseComorbiditiesNetworkMinAbsRisk,
			initial: _DiseaseComorbiditiesNetworkInitialAbsCutoff,
			max: _DiseaseComorbiditiesNetworkMaxAbsRisk
		};
	}
	
	getCYComorbiditiesNetwork() {
		return {
			nodes: [
				// jshint ignore:start
				..._DiseaseNodes,
				//..._DiseaseGroupNodes
				// jshint ignore:end
			],
			edges: _DiseaseComorbiditiesNetworkEdges
		};
	}
}
