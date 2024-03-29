'use strict';

/* globals $: false */
//import $ from 'jquery';

import tippy, {roundArrow, hideAll as tippyHideAll} from 'tippy.js';

// Singleton variables
var _Diseases;
var _DiseaseNodes;
var _DiseaseNodesByGroupId;

var _DiseaseGroups;
var _DiseaseGroupNodes;
var _DiseaseGroupsHash;

var _DiseaseComorbiditiesNetwork;

var _DiseaseComorbiditiesNetworkMinAbsRisk;
var _DiseaseComorbiditiesNetworkMaxAbsRisk;
var _DiseaseComorbiditiesNetworkInitialAbsCutoff;

var _DiseaseComorbiditiesNetworkEdges;

function distinctFilter(value,index,self) {
	return index === 0 || self.lastIndexOf(value,index-1) < 0;
}

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
					_DiseaseNodesByGroupId = {};
					_DiseaseNodes = _Diseases.map(function(dis) {
						// jshint camelcase: false
						let label = dis.name.replace(/ +/g,'\n');
						let retdis = {
							...dis,
							// Unique identifiers
							label: label,
							groupname: dis.name,
							childcount: 0,
							grandchildcount: 0,
							disease_id: dis.id,
							id: 'D'+dis.id,
							parent: 'DG'+dis.disease_group_id,
						};
						
						let retval =  {
							data: retdis,
							classes: 'D'
						};
						
						// Populating the hash of diseases grouped by disease group
						if(dis.disease_group_id in _DiseaseNodesByGroupId) {
							_DiseaseNodesByGroupId[dis.disease_group_id].push(retval);
						} else {
							_DiseaseNodesByGroupId[dis.disease_group_id] = [ retval ];
						}
						
						return retval;
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
						let label = dg.name.replace(/ +/g,'\n');
						let retdg = {
							...dg,
							label: label,
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
							...dc,
							// Unique identifiers
							id: 'DC'+dci,
							source: 'D'+dc.from_id,
							target: 'D'+dc.to_id,
						};
						delete retdc.from_id;
						delete retdc.to_id;
						
						return {
							data: retdc,
							classes: 'CM CM'+((retdc.rel_risk > 0) ? 'p' : 'n')
						};
					});
					
					let minAbsRisk = Infinity;
					let maxAbsRisk = -Infinity;
					let initialAbsCutoff = -Infinity;
					if(_DiseaseComorbiditiesNetwork.length > 0) {
						// jshint camelcase: false
						let dcme = _DiseaseComorbiditiesNetwork.map((e) => e.abs_rel_risk);
						
						// jshint camelcase: false 
						dcme.sort(function(e1,e2) { return e1 - e2; });
						dcme = dcme.filter(distinctFilter);
						minAbsRisk = dcme[0];
						maxAbsRisk = dcme[dcme.length - 1];
						
						// Selecting the initial absolute cutoff risk, based on the then biggest values
						initialAbsCutoff = dcme[Math.floor(dcme.length * 0.95)];
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
				...this.getDiseaseNodes(),
				//...this.getDiseaseGroupNodes()
			],
			edges: _DiseaseComorbiditiesNetworkEdges
		};
	}
	
	getGraphSetup() {
		if(this.params===undefined) {
			this.params = {
				name: 'concentric',
				title: 'Diseases',
				// Specific from cola algorithm
				edgeLengthVal: 45,
				animate: true,
				randomize: false,
				maxSimulationTime: 1500
			};
		}
		
		return this.params;
	}
	
	getLegendDOM() {
		let $result = $('<span style="font-size: 2rem;">Color legend (based on disease groups)</span>');
		let $legend = $('<div></div>');
		$legend.addClass('legend two-column');
		
		// For each disease group, show it
		let $elemMap = _DiseaseGroups.map((dg) => {
			let $dg = $('<div><div><i class="fas fa-circle" style="color: '+
				dg.color+
				';"></i></div><div><a>'+
				dg.name+
				'</a></div></div>');
			$dg.addClass('item');
			$dg.bind('click',() => {
				let diseaseIds = _DiseaseNodesByGroupId[dg.id].map((d) => d.data.id);
				this.cmBrowser.addSelectionByNodeId(diseaseIds);
				tippyHideAll();
				return true;
			});
			
			// The list of diseases from this disease group
			let $dSet = $('<div></div>');
			$dSet.addClass('legend-container');
			$dSet.append('<span style="font-size: 2rem;">Group ' + dg.name + '</span>');
			let $dResult = $('<div></div>');
			$dResult.addClass('legend two-column');
			$dSet.append($dResult);
			
			// And nest a tooltip with the diseases
			let tip = tippy($dg.get(0),{ // tippy options:
				content: $dSet.get(0),
				arrow: roundArrow,
				placement: 'left',
				animation: 'perspective',
				interactive: true,
				interactiveBorder: 5,
				maxWidth: '50rem',
				hideOnClick: false,
				popperOptions: {
					positionFixed: true,
				},
				trigger: 'mouseenter focus',
				//FIXME: size: 'large',
				theme: 'light',
				zIndex: 999
			});
			
			let dMap = _DiseaseNodesByGroupId[dg.id].map((d) => {
				let $dIt = $('<div><div><i class="fas fa-circle" style="color: '+
					d.data.color+
					';"></i></div><div><a>'+
					d.data.name+
					'</a></div></div>');
				$dIt.addClass('item');
				$dIt.bind('click',() => {
					this.cmBrowser.addSelectionByNodeId(d.data.id);
					tippyHideAll();
					return true;
				});
				
				return $dIt;
			});
			$dResult.append(dMap);
			
			
			return $dg;
		});
		
		$legend.append($elemMap);
		
		return [$result,$legend];
	}
	
	// Controls and their associated filters
	getControlsSetup() {
		let absRelRiskData = this.getAbsRelRiskRange();
		
		let initialAbsRelRiskVal = absRelRiskData.initial.toFixed(1);
		
		let controlsDesc = [
			{
				filter: 'edges',
				attr: 'abs_rel_risk',
				filterfn:  function(attrVal,paramVal) { return attrVal < paramVal; },
				filterOnCtx: true,
				type: 'slider',
				label: 'Cut-off on |Relative risk|',
				param: 'absRelRiskVal',
				min: absRelRiskData.min,
				max: absRelRiskData.max,
				initial: initialAbsRelRiskVal,
				scale: 'logarithmic',
				step: 0.1,
				fn: () => this.cmBrowser.batch(() => this.cmBrowser.filterOnConditions())
			},
			{
				filter: 'edges',
				attr: 'rel_risk',
				classes: 'btn-primary',
				filterfn:  function(attrVal,paramVal) { let paramValInt = parseInt(paramVal); return paramValInt !== 0 && Math.sign(attrVal) !== paramValInt; },
				filterOnCtx: true,
				type: 'radio',
				label: 'Show comorbidities',
				param: 'showComor',
				options: [
					{
						label: '-',
						title: 'Only inverse comorbidities',
						value: '-1'
					},
					{
						label: 'all',
						title: 'All kind of comorbidities',
						value: '0'
					},
					{
						label: '+',
						title: 'Only direct comorbidities',
						value: '1'
					}
				],
				initial: '0',
				layoutOpts: {},
				fn: () => this.cmBrowser.batch(() => this.cmBrowser.filterOnConditions())
			},
			//{
			//	type: 'slider',
			//	label: 'Edge length',
			//	param: 'edgeLengthVal',
			//	min: 1,
			//	max: 200,
			//	initial: 45,
			//},
			//{
			//	type: 'slider',
			//	label: 'Node spacing',
			//	param: 'nodeSpacing',
			//	min: 1,
			//	max: 50,
			//	// Specific from cola algorithm
			//	initial: 5,
			//},
			{
				type: 'button-group',
				label: 'Relayout'
			},
			//{
			//	type: 'button',
			//	label: '<i class="far fa-object-group"></i>',
			//	layoutOpts: {
			//		randomize: true
			//	},
			//	fn: () => this.toggleDiseaseGroups()
			//},
			//{
			//	type: 'button',
			//	label: '<i class="far fa-object-ungroup"></i>',
			//	layoutOpts: {
			//		randomize: true
			//	},
			//	fn: () => this.toggleDiseaseGroups()
			//},
			{
				type: 'button',
				label: '<i class="fas fa-random"></i>',
				title: 'Randomize',
				layoutOpts: {
					randomize: true,
					flow: null
				}
			},
			{
				type: 'button',
				label: '<i class="fas fa-long-arrow-alt-down"></i>',
				title: 'Relayout on y-axis',
				layoutOpts: {
					flow: {
						axis: 'y',
						minSeparation: 30
					}
				}
			},
			{
				type: 'legend',
				domNode: this.getLegendDOM(),
			}
		];
		
		return controlsDesc;
	}
	
	getNextViewSetup() {
		return { label: 'Selected diseases', idPropertyName: 'disease_id', minSelect: 2, nextView: 'patient_subgroups', nextLabel: 'See subgroups'};
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
			'('+'<i class="fas fa-circle" style="color: '+dg.color+';"></i> '+dg.name+')<br />\n'+
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
