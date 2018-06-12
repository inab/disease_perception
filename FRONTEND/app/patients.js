// Singleton variables
var _Patients;
var _PatientSubgroups;

export class Patients {
	constructor(cyContainer) {
		this.cyContainer = cyContainer;
	}
	
	// This method returns an array of promises, ready to be run in parallel
	fetch() {
		let fetchPromises = [];
		
		if(_Patients===undefined) {
			fetchPromises.push(
				fetch('api/patients', {mode: 'no-cors'})
				.then(function(res) {
					return res.json();
				})
				.then(function(decodedJson) {
					_Patients = decodedJson;
					return _Patients;
				})
			);
		}
		
		if(_PatientSubgroups===undefined) {
			fetchPromises.push(
				fetch('api/patients/subgroups', {mode: 'no-cors'})
				.then(function(res) {
					return res.json();
				})
				.then(function(decodedJson) {
					_PatientSubgroups = decodedJson;
					return _PatientSubgroups;
				})
			);
		}
		
		return fetchPromises;
	}
}
