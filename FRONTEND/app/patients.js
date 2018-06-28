'use strict';

// Singleton variables
var _Patients;

export class Patients {
	constructor(cmBrowser) {
		this.cmBrowser = cmBrowser;
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
		
		return fetchPromises;
	}
}
