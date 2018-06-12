// Singleton variables
var _Diseases;
var _DiseaseGroups;
var _DiseaseComorbiditiesNetwork;

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
					_Diseases = res.json();
					return _Diseases;
				})
			);
		}
		
		if(_DiseaseGroups===undefined) {
			fetchPromises.push(
				fetch('api/diseases/groups', {mode: 'no-cors'})
				.then(function(res) {
					_DiseaseGroups = res.json();
					return _DiseaseGroups;
				})
			);
		}
		
		if(_DiseaseComorbiditiesNetwork===undefined) {
			fetchPromises.push(
				fetch('api/diseases/comorbidities', {mode: 'no-cors'})
				.then(function(res) {
					_DiseaseComorbiditiesNetwork = res.json();
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
}
