// Singleton variables
var _Diseases;
var _DiseaseNodes;

var _DiseaseGroups;
var _DiseaseGroupNodes;
var _DiseaseGroupsHash;

var _DiseaseComorbiditiesNetwork;

var _DiseaseComorbiditiesNetworkMinAbsRisk;
var _DiseaseComorbiditiesNetworkMaxAbsRisk;
var _DiseaseComorbiditiesNetworkInitialAbsCutoff;

var _DiseaseComorbiditiesNetworkEdges;

export class Diseases {
	constructor(cmBrowser) {
		this.cmBrowser = cmBrowser;
	}
	
	// This method returns an array of promises, ready to be run in parallel
	fetch() {
		let fetchPromises = [];
		
		if(_Diseases===undefined) {
			// This is from the fetch API
			fetchPromises.push(
				fetch('api/diseases', {mode: 'no-cors'})
				.then(function(res) {
					return res.json();
				})
				.then(function(decodedJson) {
					_Diseases = decodedJson;
					_DiseaseNodes = _Diseases.map(function(dis) {
						// jshint camelcase: false 
						let retdis = {
							// jshint ignore:start
							...dis,
							// jshint ignore:end
							// Unique identifiers
							disease_id: dis.id,
							id: 'D'+dis.id,
							parent: 'DG'+dis.disease_group_id,
						};
						
						return {
							data: retdis,
							classes: 'D'
						};
					});
					return _Diseases;
				})
			);
		}
		
		if(_DiseaseGroups===undefined) {
			fetchPromises.push(
				fetch('api/diseases/groups', {mode: 'no-cors'})
				.then(function(res) {
					return res.json();
				})
				.then(function(decodedJson) {
					_DiseaseGroups = decodedJson;
					_DiseaseGroupNodes = _DiseaseGroups.map(function(dg) {
						// jshint camelcase: false 
						let retdg = {
							// jshint ignore:start
							...dg,
							// jshint ignore:end
							disease_group_id: dg.id,
							id: 'DG'+dg.id
						};
						// Unique identifiers
						return {
							data: retdg
						};
					});
					
					return _DiseaseGroups;
				})
			);
		}
		
		if(_DiseaseComorbiditiesNetwork===undefined) {
			fetchPromises.push(
				fetch('api/diseases/comorbidities', {mode: 'no-cors'})
				.then(function(res) {
					return res.json();
				})
				.then(function(decodedJson) {
					_DiseaseComorbiditiesNetwork = decodedJson;
					
					_DiseaseComorbiditiesNetworkEdges = _DiseaseComorbiditiesNetwork.map(function(dc,dci) {
						// Will be used later
						// jshint camelcase: false 
						dc.abs_rel_risk = Math.abs(dc.rel_risk);
						// Preparation
						let retdc = {
							// jshint ignore:start
							...dc
							// jshint ignore:end
						};
						// Unique identifiers
						retdc.id = 'DC'+dci;
						retdc.source = 'D'+dc.from_id;
						retdc.target = 'D'+dc.to_id;
						delete retdc.from_id;
						delete retdc.to_id;
						
						return {
							data: retdc
						};
					});
					
					let minAbsRisk = Infinity;
					let maxAbsRisk = -Infinity;
					let initialAbsCutoff = -Infinity;
					if(_DiseaseComorbiditiesNetwork.length > 0) {
						let dcme = [..._DiseaseComorbiditiesNetwork];
						
						// jshint camelcase: false 
						dcme.sort(function(e1,e2) { return e1.abs_rel_risk - e2.abs_rel_risk; });
						minAbsRisk = dcme[0].abs_rel_risk;
						maxAbsRisk = dcme[dcme.length - 1].abs_rel_risk;
						
						// Selecting the initial absolute cutoff risk, based on the then biggest values
						initialAbsCutoff = dcme[Math.floor(dcme.length * 0.95)].abs_rel_risk;
					}
					
					// Saving the range and cutoff for later processing
					_DiseaseComorbiditiesNetworkMinAbsRisk = minAbsRisk;
					_DiseaseComorbiditiesNetworkMaxAbsRisk = maxAbsRisk;
					_DiseaseComorbiditiesNetworkInitialAbsCutoff = initialAbsCutoff;
					
					return _DiseaseComorbiditiesNetwork;
				})
			);
		}
		
		return fetchPromises;
	}
	
	getDiseases() {
		return _Diseases;
	}
	
	getDiseaseNodes() {
		// Post-processing was not applied to the diseases
		if(!_DiseaseGroupsHash) {
			_DiseaseGroupsHash = {};
			_DiseaseGroups.forEach(function(dg) {
				_DiseaseGroupsHash[dg.id] = dg;
			});
			
			_DiseaseNodes.forEach(function(d) {
				// jshint camelcase: false 
				d.data.disease_group = _DiseaseGroupsHash[d.data.disease_group_id];
			});
		}
		
		return _DiseaseNodes;
	}
	
	getDiseaseGroupNodes() {
		return _DiseaseGroupNodes;
	}
	
	getComorbiditiesNetwork() {
		return _DiseaseComorbiditiesNetwork;
	}
	
	getAbsRelRiskRange() {
		return {
			min: _DiseaseComorbiditiesNetworkMinAbsRisk,
			initial: _DiseaseComorbiditiesNetworkInitialAbsCutoff,
			max: _DiseaseComorbiditiesNetworkMaxAbsRisk
		};
	}
	
	// getCYComorbiditiesNetwork
	getFetchedNetwork() {
		return {
			nodes: [
				// jshint ignore:start
				...this.getDiseaseNodes(),
				//...this.getDiseaseGroupNodes()
				// jshint ignore:end
			],
			edges: _DiseaseComorbiditiesNetworkEdges
		};
	}
	
	getGraphSetup() {
		if(this.params===undefined) {
			let absRelRiskData = this.getAbsRelRiskRange();
			
			this.params = {
				name: 'cola',
				absRelRiskVal: absRelRiskData.initial,
				// Specific from cola algorithm
				nodeSpacing: 5,
				edgeLengthVal: 45,
				animate: true,
				randomize: false,
				maxSimulationTime: 1500
			};
		}
		
		return this.params;
	}
	
	getNextViewSetup() {
		return { label: 'Visible diseases', idPropertyName: 'disease_id', nextView: 'patient_subgroups', nextLabel: 'See subgroups'};
	}
	
	makeNodeTooltipContent(node) {
		let diseaseName = node.data('name');
		let diseaseLower = diseaseName.replace(/ +/g,'-').toLowerCase();
		let icd9 = node.data('icd9');
		let icd10 = node.data('icd10');
		let dg = node.data('disease_group');
		let links = [
			{
				name: 'MedlinePlus',
				url: 'https://vsearch.nlm.nih.gov/vivisimo/cgi-bin/query-meta?v%3Aproject=medlineplus&v%3Asources=medlineplus-bundle&query=' + encodeURIComponent(diseaseName)
			},
			{
				name: 'Genetics Home Reference (search)',
				url: 'https://ghr.nlm.nih.gov/search?query='+encodeURIComponent(diseaseName)
			},
			{
				name: 'NORD (direct)',
				url: 'https://rarediseases.org/rare-diseases/' + encodeURIComponent(diseaseLower) + '/'
			},
			{
				name: 'Genetics Home Reference (direct)',
				url: 'https://ghr.nlm.nih.gov/condition/' + encodeURIComponent(diseaseLower)
			},
			{
				name: 'Wikipedia (direct)',
				url: 'https://en.wikipedia.org/wiki/' + encodeURIComponent(diseaseName)
			}
		];
		
		if(icd10 !== '-') {
			links.unshift({
				name: 'ICDList (ICD10)',
				url: 'https://icdlist.com/icd-10/' + encodeURIComponent(icd10)
			});
		}
		
		if(icd9 !== '-') {
			links.unshift({
				name: 'ChrisEndres (ICD9)',
				url: 'http://icd9.chrisendres.com/index.php?action=child&recordid=' + encodeURIComponent(icd9)
			});
		}
		
		let content = document.createElement('div');
		content.setAttribute('style','font-size: 1.3em;');
		
		//content.innerHTML = 'Tippy content';
		content.innerHTML = '<b>'+diseaseName+'</b>'+' ICD9: '+icd9 + ' ICD10: ' + icd10 + '<br />\n'+
			'('+'<i class="fa fa-circle" style="color: '+dg.color+';"></i> '+dg.name+')<br />\n'+
			'<div style="text-align: left;">' +
			links.map(function(link) {
				return '<a target="_blank" href="' + link.url + '">' + link.name + '</a>';
			}).join('<br />\n') +
			'</div>';

		return content;
	}
	
	makeEdgeTooltipContent(edge) {
		let content = document.createElement('div');
		content.setAttribute('style','font-size: 1.3em;text-align: left;');
		
		let source = edge.source();
		let target = edge.target();
		
		
		content.innerHTML = '<b><u>Relative risk</u></b>: ' + edge.data('rel_risk') +
			'<div><b>Source</b>: '+source.data('name') + '<br />\n' +
			'<b>Target</b>: '+target.data('name')+'</div>';
		return content;
	}
}
