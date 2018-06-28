'use strict';

// Singleton variables
var _Studies;

export class Studies {
	constructor(cmBrowser) {
		this.cmBrowser = cmBrowser;
	}
	
	// This method returns an array of promises, ready to be run in parallel
	fetch() {
		let fetchPromises = [];
		
		if(_Studies===undefined) {
			fetchPromises.push(
				fetch('api/studies', {mode: 'no-cors'})
				.then(function(res) {
					return res.json();
				})
				.then(function(decodedJson) {
					_Studies = decodedJson;
					return _Studies;
				})
			);
		}
		
		return fetchPromises;
	}
}
