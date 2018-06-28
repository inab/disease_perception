'use strict';

// Singleton variables
var _Drugs;

export class Drugs {
	constructor(cmBrowser) {
		this.cmBrowser = cmBrowser;
	}
	
	// This method returns an array of promises, ready to be run in parallel
	fetch() {
		let fetchPromises = [];
		
		if(_Drugs===undefined) {
			fetchPromises.push(
				fetch('api/drugs', {mode: 'no-cors'})
				.then(function(res) {
					return res.json();
				})
				.then(function(decodedJson) {
					_Drugs = decodedJson;
					return _Drugs;
				})
			);
		}
		
		return fetchPromises;
	}
}
