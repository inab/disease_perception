// Singleton variables
var _Studies;

export class Studies {
	constructor(cyContainer) {
		this.cyContainer = cyContainer;
	}
	
	// This method returns an array of promises, ready to be run in parallel
	fetch() {
		let fetchPromises = [];
		
		if(_Studies===undefined) {
			fetchPromises.push(
				fetch('api/studies', {mode: 'no-cors'})
				.then(function(res) {
					_Studies = res.json();
					return _Studies;
				})
			);
		}
		
		return fetchPromises;
	}
}
