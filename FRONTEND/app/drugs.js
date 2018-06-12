// Singleton variables
var _Drugs;

export class Drugs {
	constructor(cyContainer) {
		this.cyContainer = cyContainer;
	}
	
	// This method returns an array of promises, ready to be run in parallel
	fetch() {
		let fetchPromises = [];
		
		if(_Drugs===undefined) {
			fetchPromises.push(
				fetch('api/drugs', {mode: 'no-cors'})
				.then(function(res) {
					_Drugs = res.json();
					return _Drugs;
				})
			);
		}
		
		return fetchPromises;
	}
}
