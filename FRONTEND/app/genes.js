'use strict';

// Singleton variables
var _Genes;
var _GeneNodes;

export class Genes {
	constructor(cmBrowser) {
		this.cmBrowser = cmBrowser;
	}
	
	// This method returns an array of promises, ready to be run in parallel
	fetch() {
		let fetchPromises = [];
		
		if(_Genes===undefined) {
			fetchPromises.push(
				fetch('api/genes', {mode: 'no-cors'})
				.then(function(res) {
					return res.json();
				})
				.then(function(decodedJson) {
					_Genes = decodedJson;
					_GeneNodes = _Genes.map(function(gene) {
						// jshint camelcase: false
						let retgene = {
							...gene,
							// Unique identifiers
							name: gene.gene_symbol,
							id: gene.gene_symbol
						};
						
						return {
							data: retgene,
							classes: 'G'
						};
					});
					return _Genes;
				})
			);
		}
		
		return fetchPromises;
	}
	
	getGenes() {
		return _Genes;
	}
	
	getGeneNodes() {
		return _GeneNodes;
	}
}
