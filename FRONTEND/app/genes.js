// Singleton variables
var _Genes;

export class Genes {
	constructor(cyContainer) {
		this.cyContainer = cyContainer;
	}
	
	// This method returns an array of promises, ready to be run in parallel
	fetch() {
		let fetchPromises = [];
		
		if(_Genes===undefined) {
			fetchPromises.push(
				fetch('api/genes', {mode: 'no-cors'})
				.then(function(res) {
					_Genes = res.json();
					return _Genes;
				})
			);
		}
		
		return fetchPromises;
	}
}
