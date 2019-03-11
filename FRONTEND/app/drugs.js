'use strict';

// Singleton variables
var _Drugs;
var _DrugNodes;

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
					_DrugNodes = _Drugs.map(function(drug) {
						// jshint camelcase: false
						let retdrug = {
							...drug,
							// Unique identifiers
							drug_id: drug.id,
							id: 'Dr'+drug.id,
						};
						
						return {
							data: retdrug,
							classes: 'Dr'
						};
					});
					return _Drugs;
				})
			);
		}
		
		return fetchPromises;
	}
	
	getDrugs() {
		return _Drugs;
	}
	
	getDrugNodes() {
		return _DrugNodes;
	}
}
