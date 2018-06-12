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
					_Patients = res.json();
					return _Patients;
				})
			);
		}
		
		if(_PatientSubgroups===undefined) {
			fetchPromises.push(
				fetch('api/patients/subgroups', {mode: 'no-cors'})
				.then(function(res) {
					_PatientSubgroups = res.json();
					return _PatientSubgroups;
				})
			);
		}
		
		return fetchPromises;
	}
}
