'use strict';

/* globals $: false */
//import $ from 'jquery';

import _ from 'lodash';

import 'bootstrap';
import 'bootstrap-slider';
//import typeahead from 'typeahead.js/dist/typeahead.jquery.js';
//import Bloodhound from 'typeahead.js/dist/bloodhound.js';
import Bloodhound from 'typeahead.js';
import FastClick from 'fastclick';

import cytoscape from 'cytoscape';

// Pan/Zoom (disabled)
//import panzoom from 'cytoscape-panzoom';
//panzoom(cytoscape);

// Graph layouts
import cycola from 'cytoscape-cola';
cytoscape.use( cycola );
import cycosebilkent from 'cytoscape-cose-bilkent';
cytoscape.use( cycosebilkent );
import cydagre from 'cytoscape-dagre';
cytoscape.use( cydagre );
import cyklay from 'cytoscape-klay';
cytoscape.use( cyklay );

// Plugin to export as SVG
import cysvg from 'cytoscape-svg';
cytoscape.use( cysvg );

// Tooltips attached to graph elements
import popper from 'cytoscape-popper';
cytoscape.use( popper );
import tippy from 'tippy.js';

// toDataURL support
import urlfy from 'toDataURL';

// Internal code
import { Diseases } from './diseases';
import { Patients } from './patients';
import { PatientSubgroups } from './patient_subgroups';
import { Genes } from './genes';
import { Drugs } from './drugs';
import { Studies } from './studies';

// Sleeping with promises
//function sleep(millis) {
//	return new Promise((resolve) => setTimeout(resolve,millis));
//}

export class ComorbiditiesBrowser {
	constructor(setup) {
		// Create the object holding all the ui elements
		let ui = this.ui = {};
		let uiElems = [];
		
		// The graph container
		ui.$graph = $(setup.graph);
		
		// Create the graph title
		ui.$graphTitle = $('<div></div>');
		ui.$graphTitle.attr('id','graph-title');
		ui.$graphTitle.addClass('graph-title cmui');
		uiElems.push(ui.$graphTitle);
		
		// Create the history
		this.history = [];
		this.historyPointer = -1;
		
		// Create the history management buttons
		ui.$historyBack = $('<button><i class="far fa-arrow-alt-circle-left" aria-hidden="true" title="Previous view"></i></button>');
		ui.$historyBack.attr('id','history-back');
		ui.$historyBack.addClass('cmui button btn btn-default');
		ui.$historyBack.on('click',() => this.historyGoBack());
		ui.$historyBack.prop('disabled',true);
		uiElems.push(ui.$historyBack);
		
		ui.$unselectAll = $('<button><i class="fas fa-sitemap" aria-hidden="true" title="Unselect all"></i></button>');
		ui.$unselectAll.attr('id','unselect-all');
		ui.$unselectAll.addClass('cmui button btn btn-default');
		ui.$unselectAll.on('click',() => this.unselectAll());
		ui.$unselectAll.prop('disabled',true);
		uiElems.push(ui.$unselectAll);
		
		ui.$historyForward = $('<button><i class="far fa-arrow-alt-circle-right" aria-hidden="true" title="Next view"></i></button>');
		ui.$historyForward.addClass('cmui button btn btn-default');
		ui.$historyForward.attr('id','history-forward');
		ui.$historyForward.on('click',() => this.historyGoForward());
		ui.$historyForward.prop('disabled',true);
		uiElems.push(ui.$historyForward);
		
		// The search button
		ui.$search = $('<button><i class="fas fa-search" aria-hidden="true" title="Search"></i></button>');
		ui.$search.addClass('cmui button');
		ui.$search.attr('id','search');
		//ui.$search.prop('disabled',true);
		uiElems.push(ui.$search);
		
		// The body of the search tooltip, to be used by tippy
		ui.$searchBody = $('<div></div>');
		ui.$searchBody.addClass('search-container');

		ui.$searchField = $('<input type="text" placeholder="Diseases">');
		ui.$searchField.addClass('form-control typeahead');
		//ui.$searchField.addClass('typeahead');
		
		ui.$searchBody.append(ui.$searchField);
		ui.$searchBody.hide();
		
		let tipSearch = tippy(ui.$search.get(0),{ // tippy options:
			content: ui.$searchBody.get(0),
			arrow: true,
			arrowType: 'round',
			placement: 'right-start',
			animation: 'perspective',
			interactive: true,
			interactiveBorder: 5,
			hideOnClick: false,
			multiple: false,
			trigger: 'mouseenter focus',
			size: 'large',
			theme: 'light',
			zIndex: 999,
			onShown: () => {
				ui.$searchField.focus();
			}
		});
		
		ui.$search.on('mouseenter focus',() => ui.$searchBody.show());
		ui.$search.on('click', () => ui.$searchBody.toggle());
		ui.$searchBody.on('mouseenter focus',() => ui.$searchBody.show());
		ui.$searchBody.on('mouseleave unfocus',() => ui.$searchBody.hide());
		
		// The legend button
		ui.$legend = $('<button><i class="fas fa-info-circle" aria-hidden="true"></i></button>');
		ui.$legend.addClass('cmui button');
		ui.$legend.attr('id','legend');
		ui.$legend.hide();
		uiElems.push(ui.$legend);
		
		// The body of the legend, to be used by tippy
		ui.$legendBody = $('<div></div>');
		ui.$legendBody.addClass('legend-container');
		
		let tip = tippy(ui.$legend.get(0),{ // tippy options:
			content: ui.$legendBody.get(0),
			arrow: true,
			arrowType: 'round',
			placement: 'bottom-end',
			animation: 'perspective',
			interactive: true,
			interactiveBorder: 5,
			hideOnClick: false,
			multiple: false,
			trigger: 'mouseenter focus',
			size: 'large',
			theme: 'light',
			zIndex: 999
		});
		
		// Snapshots
		ui.$snapshot = $('<button><i class="far fa-images" aria-hidden="true" title="Save network view snapshot"></i></button>');
		ui.$snapshot.addClass('cmui button');
		//ui.$snapshot.addClass('cmui button button btn btn-default');
		ui.$snapshot.attr('id','snapshot');
		uiElems.push(ui.$snapshot);
		
		let $snapshotBody = $('<div></div>');
		$snapshotBody.addClass('snapshot-container');
		
		// Save PNG snapshot
		$snapshotBody.append('PNG');
		ui.$snapshotPNG = $('<a><i class="far fa-file-image" aria-hidden="true" title="Save as PNG network view snapshot"></i></a>');
		ui.$snapshotPNG.addClass('cmui-inline button btn btn-default');
		ui.$snapshotPNG.attr('id','snapshotPNG');
		ui.$snapshotPNG.on('click',() => this.saveSnapshotPNG());
		$snapshotBody.append(ui.$snapshotPNG);
		
		// Save SVG snapshot
		$snapshotBody.append('SVG');
		ui.$snapshotSVG = $('<a><i class="fas fa-image" aria-hidden="true" title="Save as SVG network view snapshot"></i></a>');
		ui.$snapshotSVG.addClass('cmui-inline button btn btn-default');
		ui.$snapshotSVG.attr('id','snapshotSVG');
		ui.$snapshotSVG.on('click',() => this.saveSnapshotSVG());
		$snapshotBody.append(ui.$snapshotSVG);
		
		let tipSnapshot = tippy(ui.$snapshot.get(0),{ // tippy options:
			content: $snapshotBody.get(0),
			arrow: true,
			arrowType: 'round',
			placement: 'bottom-end',
			animation: 'perspective',
			interactive: true,
			interactiveBorder: 5,
			hideOnClick: false,
			multiple: false,
			trigger: 'mouseenter focus',
			size: 'large',
			theme: 'light',
			zIndex: 999
		});
		
		// Save shown graph in Cytoscape.js format
		ui.$saveNetwork = $('<a><i class="fas fa-chart-area" aria-hidden="true" title="Save network as Cytoscape.json"></i></a>');
		ui.$saveNetwork.addClass('cmui button button btn btn-default');
		ui.$saveNetwork.attr('id','save-network');
		ui.$saveNetwork.on('click',() => this.saveNetwork());
		uiElems.push(ui.$saveNetwork);
		
		
		// The right panel container
		ui.$config = $(setup.configPanel);
		// The right panel toggle container
		ui.$configToggle = $(setup.configPanelToggle);
		
		// Event handler to show/hide the config container
		ui.$configToggle.on('click', () => {
			$('body').toggleClass('config-closed');
			
			if(this.cy) {
				this.cy.resize();
			}
			if(this.layout) {
				this.layout.run();
			}
		});
		
		// Event handler to resize the graph on window shape change
		$(window).on('resize',() => {
			if(this.cy) {
				this.cy.resize();
			}
			if(this.layout) {
				this.layout.run();
			}
		});
		
		// Controls within the config panel
		ui.$controls = $(setup.graphControls);
		
		// Loading state controls
		ui.$loading = $(setup.loading);
		ui.$appLoading = $(setup.appLoading);
		
		
		
		// A modal (to be used)
		ui.$modal = $(setup.modal);
		
		// Now, all the dynamically created elements are placed after the graph
		ui.$graph.after(uiElems);
		
		// Setting up the typeahead component
		ui.bloodhound = new Bloodhound({
			identify: function(o) { return o.data.id; },
			queryTokenizer: Bloodhound.tokenizers.whitespace,
			datumTokenizer: function(o) { return Bloodhound.tokenizers.whitespace(o.data.label);}
		});
		
		ui.$searchField.typeahead({
			hint: false,
			highlight: true,
			minLenght: 0,
			classNames: {
				menu: 'dropdown-menu'
			}
		},{
			name: 'nodes',
			display: function(o) { return o.data.label; },
			source: ui.bloodhound,
			templates: {
				notFound: '<span style="font-style: italic;">No match</span>',
				suggestion: (node) => {
					let unavailable = this.filteredEles.getElementById(node.data.id).length > 0;
					let theNode = '<div><i class="fas fa-circle" style="color: '+
						node.data.color+
						';"></i> ';
					theNode += '<span class="term-' +
						(unavailable ? 'unavailable' : 'available') + '">' +
						node.data.name + '</span></div>';
					return theNode;
				}
			}
		}).bind('typeahead:select',(ev,suggestion) => {
			this.addSelectionByNodeId(suggestion.data.id);
			ui.$searchField.typeahead('val','');
			tipSearch.hide();
		}).on('keyup', (e) => {
			switch(e.keyCode) {
				case 13:
					// Do something
					let fieldVal = ui.$searchField.typeahead('val');
					if(fieldVal.length > 0) {
						ui.bloodhound.search(fieldVal,(res) => {
							if(res.length > 0) {
								this.addSelectionByNodeId(res[0].data.id);
								ui.$searchField.typeahead('val','');
								tipSearch.hide();
							}
						});
					}
					break;
				case 27:
					ui.$searchField.typeahead('val','');
					tipSearch.hide();
					break;
			}
		});

		
		// The list of disposable configuration widgets
		this.configWidgets = [];
		this.hPanel = null;
		
		// Fix for old mobile browsers
		FastClick.attach( document.body );
		
		// Preparing the views
		// jshint camelcase: false 
		this.views = {
			diseases: new Diseases(this),
			patients: new Patients(this),
			patient_subgroups: new PatientSubgroups(this),
			genes: new Genes(this),
			drugs: new Drugs(this),
			studies: new Studies(this),
		};
	}

	switchView(viewName, ...viewParams) {
		if(!(viewName in this.views)) {
			console.error('This should not happen!!!');
		}
		
		// Saving the parameters
		if(this.historyPointer > -1) {
			this.saveLayoutParams(this.params);
			this.saveSelectedNodes();
		}
		
		// Should we remove the history by replacing it?
		if(this.historyPointer+1 !== this.history.length) {
			this.history.splice(this.historyPointer+1);
		}
		
		// Now, populate the history
		this.history.push({
			viewName: viewName,
			viewParams: viewParams,
			layoutParams: null,
			selectedNodeIds: []
		});
		this.historyPointer++;
		
		this.switchHistoryView();
	}
	
	switchHistoryView(historyId=-1) {
		this.ui.$loading.removeClass('loaded');
		this.ui.$legend.hide();
		if(historyId===-1) {
			historyId = this.historyPointer;
		} else {
			this.historyPointer = historyId;
		}
		
		this.ui.$historyBack.prop('disabled',this.historyPointer===0);
		this.ui.$historyForward.prop('disabled',this.historyPointer+1 === this.history.length);
		this.ui.$unselectAll.prop('disabled',true);
		
		let viewName = this.history[historyId].viewName;
		let viewParams = this.history[historyId].viewParams;
		
		this.viewName = viewName;
		let currentView = this.currentView = this.views[viewName];
		
		// Preparing the initial data fetch
		let fetchPromises = this.fetch();
		
		let viewPromises = currentView.fetch(...viewParams);
		viewPromises.forEach((e) => fetchPromises.push(e));
		
		// Now, issuing the fetch itself, and then the layout
		Promise.all(fetchPromises)
		.then((dataArray) => {
			this.doLayout(dataArray);
			let selected = this.getSavedSelectedNodes();
			if(selected.nonempty()) {
				selected.select();
			}
			this.ui.$loading.addClass('loaded');
			this.ui.$appLoading.addClass('loaded');
		});
	}
	
	getSavedLayoutParams() {
		return this.history[this.historyPointer].layoutParams;
	}
	
	saveLayoutParams(params) {
		this.history[this.historyPointer].layoutParams = params;
	}
	
	getSavedSelectedNodes() {
		let selected = this.cy.collection();
		
		this.history[this.historyPointer].selectedNodeIds.forEach((nId) => {
			selected.merge(this.cy.getElementById(nId));
		});
		
		return selected;
	}
	
	saveSelectedNodes() {
		let nodeIds = this.cy.nodes('node:selected').map((n) => n.id());
		this.history[this.historyPointer].selectedNodeIds = nodeIds;
	}
	
	historyGoBack() {
		if(this.historyPointer > 0) {
			this.saveLayoutParams(this.params);
			this.saveSelectedNodes();
			this.switchHistoryView(this.historyPointer-1);
		}
	}
	
	historyGoForward() {
		if(this.historyPointer+1 < this.history.length) {
			this.saveLayoutParams(this.params);
			this.saveSelectedNodes();
			this.switchHistoryView(this.historyPointer+1);
		}
	}
	
	getViewId() {
		return this.history[this.historyPointer].viewName;
	}
	
	saveSnapshotPNG() {
		this.ui.$snapshotPNG.attr('download','disease-perception_'+this.getViewId()+'.png');
		this.ui.$snapshotPNG.attr('href',this.cy.png({full: true, scale: 2}));
	}
	
	saveSnapshotSVG() {
		this.ui.$snapshotSVG.attr('download','disease-perception_'+this.getViewId()+'.svg');
		this.ui.$snapshotSVG.attr('href',urlfy.toDataURL(this.cy.svg({full: true}),'application/xml+svg'));
	}
	
	saveNetwork() {
		this.ui.$saveNetwork.attr('download','disease-perception_'+this.getViewId()+'.json');
		this.ui.$saveNetwork.attr('href',urlfy.toDataURL(JSON.stringify(this.cy.json()),'application/json'));
	}
	
	makeCy(container, style, graphData) {
		if(this.cy) {
			this.layout.stop();
			this.layout.destroy();
			this.layout = null;
			this.unHighlighted = null;
			this.prevHighlighted = null;
			this.filteredEles = null;
			this.filtersDesc = null;
			this.cy.destroy();
			this.cy = null;
			this.ctxHandlers = null;
		}
		
		this.filtersDesc = {
			edges: [],
			nodes: []
		};
		
		this.ctxHandlers = {
			edges: [],
			nodes: []
		};
		
		this.cy = cytoscape({
			container: container,
			//style: style,
			style: [
			//	...graphData.style,
				...style
			],
			elements: graphData
		});
		
		this.cy.on('layoutstart', () => { this.running = true; });
		this.cy.on('layoutstop', () => { this.running = false; });
	}
	
	makeLayout(opts) {
		for(let i in opts){
			this.params[i] = opts[i];
		}
		
		this.params.randomize = false;
		// Disabled for now, as it hogs the CPU
		//this.params.edgeLength = (e) => {
		//	return this.params.edgeLengthVal / e.data('rel_risk'); 
		//};
		
		
		// Setting the layout as such
		this.layout = this.cy.layout(this.params);
	}
	
		
	makeSlider(opts,$parent) {
		let $input = $('<input></input>');
		let $param = $('<div class="param"></div>');
		
		$param.append('<span class="label label-default">'+ opts.label +'</span>');
		
		// Is the initial value already set?
		let initialValue = null;
		if(opts.param in this.params) {
			initialValue = this.params[ opts.param ];
		} else {
			initialValue = opts.initial;
			// Setting the initial value
			this.params[ opts.param ] = initialValue;
		}
		let $dataLabel = $('<span class="label label-info">'+ initialValue +'</span>');
		$param.append($dataLabel);
		$param.append($input);
				
		let scale = opts.scale === undefined ? 'linear' : opts.scale;
		let step = opts.step ? opts.step : 1;
		
		let minVal = Math.floor(opts.min);
		let maxVal = Math.ceil(opts.max);
		
		let p = $input.slider({
			min: minVal,
			max: maxVal,
			//ticks: [minVal,initialValue,maxVal],
			//ticks_labels: [minVal,initialValue,maxVal],
			scale: scale,
			step: step,
			value: initialValue
		}).on('slideStop', _.throttle( () => {
			this.params[ opts.param ] = p.getValue();
			$dataLabel.html(p.getValue());
			
			this.layout.stop();
			
			if(opts.fn) {
				opts.fn();
			}
			
			this.makeLayout();
			this.layout.run();
		}, 16 ) ).data('slider');
		
		$parent.append($param);
		
		// The control itself is more useful
		return $input;
	}
	
	makeCheckbox(opts,btnParam) {
		let checkedVal = ('checkedVal' in opts) ? opts.checkedVal : true;
		let uncheckedVal = ('uncheckedVal' in opts) ? opts.uncheckedVal : false;
		
		let $checkboxContainer = $('<div style="display: flex;"></div>');
		let $checkbox = $('<input type="checkbox"></input>');
		$checkbox.button();
		
		let initial = null;
		if(opts.param in this.params) {
			initial = this.params[ opts.param ] === checkedVal;
		} else {
			initial = opts.initial;
		}
		if(initial) {
			$checkbox.attr('checked','checked');
			$checkbox.toggle();
		}
		$checkbox.on('change',() => {
			this.params[ opts.param ] = $checkbox.is(':checked') ? checkedVal : uncheckedVal;
			
			if(opts.layoutOpts) {
				this.layout.stop();
			}
			
			if(opts.fn) {
				opts.fn();
			}
			
			if(opts.layoutOpts) {
				this.makeLayout(opts.layoutOpts);
				this.layout.run();
			}
		});
		
		let $cont = $('<div style="white-space: nowrap"></div>');
		$cont.append($checkbox);
		$checkboxContainer.append($cont);
		
		let $label = $('<div>'+opts.label+'</div>');
		$checkboxContainer.append($label);
		btnParam.append( $checkboxContainer );
		
		return $checkbox;
	}
	
	makeButton(opts,btnParam) {
		let optsLabel = opts.label ? opts.label : opts.value;
		let $button = $('<button type="button" class="btn btn-default">' + optsLabel + '</button>');
		if(opts.classes) {
			$button.addClass(opts.classes);
		}
		
		if(opts.value) {
			$button.val(opts.value);
		}
		
		$button.on('click', () => {
			if(opts.param) {
				this.params[ opts.param ] = $button.val();
			}
			
			if(opts.layoutOpts) {
				this.layout.stop();
			}
			
			if(opts.fn) {
				opts.fn();
			}
			
			if(opts.layoutOpts) {
				this.makeLayout(opts.layoutOpts);
				this.layout.run();
			}
		});
		
		btnParam.append( $button );
		
		return $button;
	}
	
	makeSelectButtons(opts,btnParam) {
		let $param = $('<div class="param"></div>');
		
		$param.append('<span class="label label-default">'+ opts.label +'</span>');
		
		let $buttonGroup = $('<div class="btn-group" role="group" aria-label="'+opts.label+'"></div>');
		$param.append($buttonGroup);
		
		let iniVal = this.params[ opts.param ];
		opts.options.forEach((opt) => {
			opt.initiallyToggled = opt.value === iniVal;
			
			this.makeButton(opt,$buttonGroup);
		});
		btnParam.append( $param );
		
		return $param;
	}
	
	makeSelectDropdown(opts,btnParam) {
		btnParam.append('<span class="label label-default">'+ opts.label +'</span>');
		
		let $buttonGroup = $('<div class="btn-group" style="width: 100%; margin-bottom: 1em;" aria-label="'+opts.label+'"></div>');
		btnParam.append($buttonGroup);
		
		let $dropdownButton = $('<button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false"></button>');
		$buttonGroup.append($dropdownButton);
		
		let $dropdownCaret = $('<button type="button" class="btn btn-info dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false"><span class="caret"></span><span class="sr-only">Toggle Dropdown</span></button>');
		$buttonGroup.append($dropdownCaret);
		
		let $optList = $('<ul class="dropdown-menu"></ul>');
		$buttonGroup.append($optList);
		
		let iniVal = this.params[ opts.param ];
		opts.options.forEach((opt) => {
			let optLabel = opt.label ? opt.label : opt.value;
			if(opt.value === iniVal) {
				$dropdownButton.html(optLabel);
			}
			
			let $option = $('<li><a href="#">' + optLabel + '</li>');
			$option.val(opt.value);
			
			$option.on('click', () => {
				if(opt.param) {
					this.params[ opt.param ] = opt.value;
				} else if(opts.param) {
					this.params[ opts.param ] = opt.value;
				}
				$dropdownButton.html($option.html());
				
				this.layout.stop();
				
				if(opts.fn) {
					opts.fn();
				}
				
				if(opt.fn) {
					opt.fn();
				}
				
				this.makeLayout(opts.layoutOpts);
				this.layout.run();
			});
			
			$optList.append( $option );
		});
		
		return $buttonGroup;
	}
	
	makeNodeOption(node,isInitiallyChecked,opts) {
		let $option = $('<div style="display: flex;"></div>');
		let $nodeOption = $('<input type="checkbox"></input>');
		$nodeOption.data(opts.idPropertyName,node.data(opts.idPropertyName));
		$nodeOption.button();
		if(isInitiallyChecked) {
			$nodeOption.attr('checked','checked');
			$nodeOption.toggle();
		}
		$nodeOption.on('change',() => {
			this.updateSelectedNodesCount($option.parent().find('input[type="checkbox"]:checked'));
		});
		
		let $cont = $('<div style="white-space: nowrap"></div>');
		$cont.append($nodeOption);
		$cont.append('<i class="fas fa-circle" style="vertical-align: text-top; color: '+node.data('color')+';"></i>');
		$option.append($cont);
		
		//$option.append($nodeOption);
		//$option.append('<i class="fas fa-circle" style="color: '+node.data('color')+';"></i>');
		let $label = $('<div>'+node.data('name')+'</div>');
		if(!isInitiallyChecked) {
			$label.css('font-style','italic');
		}
		$option.append($label);
		return $option;
	}
	
	updateSelectedNodesCount(nodes) {
		if(this.hPanel) {
			let hPanel = this.hPanel;
			hPanel.$nodeListLabel.empty();
			hPanel.$nodeListLabel.append(nodes.length);
			hPanel.$nodeListNextViewButton.prop('disabled', nodes.length < this.nextViewSetup.minSelect);
		}
	}
	
	registerConfigWidget($widget) {
		this.ui.$config.append($widget);
		this.configWidgets.push($widget);
	}
	
	makeSelectedNodesView(opts) {
		let hPanel = this.hPanel = {};
		let $selectedNodesView = hPanel.$selectedNodesView = $('<div class="param"></div>');
		$selectedNodesView.hide();
		
		// The title
		$selectedNodesView.append('<span class="label label-default">' + opts.label + '</span>');
		
		// The number of selected nodes
		let $nodeListLabel = hPanel.$nodeListLabel = $('<span class="label label-info"></span>');
		
		$selectedNodesView.append($nodeListLabel);
		
		// The container of the selected nodes
		let $nodeList = hPanel.$nodeList = $('<div style="overflow-y:auto;max-height: 25%;background-color:white;color:black;"></div>');
		$nodeList.data('opts',opts);
		$nodeList.hide();
		
		// This button should check or uncheck all the elements
		// jshint unused:false
		let $selectAll = this.makeButton({
				classes: 'btn-xs',
				label: '<i class="far fa-check-square" title="Select all"></i>',
				fn: () => {
					$nodeList.find('input[type="checkbox"]').prop('checked',true);
					this.updateSelectedNodesCount($nodeList.find('input[type="checkbox"]:checked'));
				},
			},$selectedNodesView);
		let $selectNone = this.makeButton({
				classes: 'btn-xs',
				label: '<i class="far fa-square" title="Unselect all"></i>',
				fn: () => {
					$nodeList.find('input[type="checkbox"]').prop('checked',false);
					this.updateSelectedNodesCount($nodeList.find('input[type="checkbox"]:checked'));
				},
			},$selectedNodesView);
		
		let $nodeListNextViewButton = hPanel.$nodeListNextViewButton = $('<input type="button" class="btn btn-default btn-xs" value="'+opts.nextLabel+'" />');
		$nodeListNextViewButton.on('click',() => {
			let nextViewIds = $nodeList.find('input[type="checkbox"]:checked').toArray().map((check) => {
				let checkbox = $(check);
				
				return checkbox.data(opts.idPropertyName);
			});
			this.switchView(opts.nextView,nextViewIds);
		});
		
		$selectedNodesView.append($nodeListNextViewButton);
		
		this.registerConfigWidget($selectedNodesView);
		
		// The container must go here
		this.registerConfigWidget($nodeList);
	}
	
	updateHighlightSubpanel(nodes) {
		this.updateSelectedNodesCount(nodes);
		if(this.hPanel) {
			let hPanel = this.hPanel;
			if(nodes.nonempty()) {
				hPanel.$selectedNodesView.show();
				hPanel.$nodeList.show();
				let opts = hPanel.$nodeList.data('opts');
				
				hPanel.$nodeList.empty();
				
				nodes.forEach((n) => {
					if(!n.isParent()) {
						let $option = this.makeNodeOption(n,true,opts);
						
						hPanel.$nodeList.append($option);
					}
				});
				
				this.prevHighlighted.nodes().difference(nodes).forEach((n) => {
					if(!n.isParent()) {
						let $option = this.makeNodeOption(n,false,opts);
						
						hPanel.$nodeList.append($option);
					}
				});
			} else {
				hPanel.$selectedNodesView.hide();
				hPanel.$nodeList.hide();
			}
		}
	}
	
	
	highlight(nodes) {
		// Restore what it was hidden
		this.cy.batch(() => {
			if(this.unHighlighted) {
				this.unHighlighted.restore();
				this.unHighlighted = null;
			}
			
			this.prevHighlighted = nodes;
			
			if(nodes.nonempty()) {
				let nhood = nodes.closedNeighborhood();
				
				nhood.merge(nhood.edgesWith(nhood));
				nhood.merge(nhood.ancestors());
				
				this.prevHighlighted = nhood;
				
				this.unHighlighted = this.cy.elements().not( nhood ).remove();
			}
			this.layout.stop();
			this.updateHighlightSubpanel(nodes);
			this.makeLayout({ randomize: true});
			this.layout.run();
		});
	}


	filterOnConditions() {
		// Recording the already selected nodes
		let selectedNodes = this.cy.nodes('node:selected');
		this.disableHighlightUpdates = true;
		selectedNodes.unselect();
		
		this.prevHighlighted = null;
		if(this.unHighlighted && this.unHighlighted.nonempty()) {
			this.unHighlighted.restore();
			this.unHighlighted = null;
		}
		
		if(this.filteredEles && this.filteredEles.nonempty()) {
			this.filteredEles.restore();
			this.filteredEles = null;
		}
		
		// Applying the initial filtering
		
		// On nodes
		if(this.filtersDesc && this.filtersDesc.nodes) {
			this.filteredEles = this.cy.nodes((e) => {
				return this.filtersDesc.nodes.some((f) => {
					return f.filterfn(e.data(f.attr),this.params[f.param]);
				});
			}).remove();
		} else {
			this.filteredEles = this.cy.collection();
		}
		
		// On arcs
		if(this.filtersDesc && this.filtersDesc.edges) {
			this.filteredEles.merge(this.cy.edges((e) => {
				return this.filtersDesc.edges.some((f) => {
					return f.filterfn(e.data(f.attr),this.params[f.param]);
				});
			}).remove());
		}
		
		// Now, remove the filtered or orphaned nodes
		this.filteredEles.merge(this.cy.nodes((n) => {
			return !n.isParent() && (n.degree(true) === 0);
			//return n.degree(true) === 0;
		}).remove());
		
		// And, at last, highlight again (if possible)
		this.disableHighlightUpdates = false;
		if(selectedNodes.nonempty()) {
			let newIntersection = this.cy.nodes().intersection(selectedNodes);
			if(newIntersection.nonempty()) {
				// The callback which highlights should be fired by this action
				newIntersection.select();
			} else {
				this.cy.emit('unselect',[true]);
			}
		}
	}
	
	// This method is not working as expected, so disable it for now
	toggleDiseaseGroups() {
		if(this.hiddenDiseaseGroups) {
			this.hiddenDiseaseGroups.restore();
			this.hiddenDiseaseGroups = null;
		} else {
			// There could be disease groups in hidden nodes
			if(this.filteredEles) {
				this.filteredEles.restore();
				this.filteredEles = null;
			}
			
			this.hiddenDiseaseGroups = this.cy.nodes((n) => {
				return n.isParent();
			}).remove();
			this.hiddenDiseaseGroups.filter((n) => { return !n.isParent(); }).restore();
		}
		
		this.filterOnConditions();
	}
	
	makeLegend(opts) {
		this.ui.$legendBody.empty();
		this.ui.$legendBody.append(opts.domNode);
		this.ui.$legend.show();
		
		return this.ui.$legendBody;
	}
	
	initializeControls() {
		let $controls = this.ui.$controls;
		$controls.empty();
		
		if(this.configWidgets.length > 0) {
			this.configWidgets.forEach(function($widget) {
				$widget.remove();
			});
			
			this.configWidgets = [];
		}
		
		// First and foremost, set the title
		this.ui.$graphTitle.html(this.params.title);
		
		let graphLayoutSelect = {
			label: 'Graph Layouts',
			param: 'name',
			options: [
				{
					label: 'Concentric',
					value: 'concentric'
				},
				{
					label: 'Cola',
					value: 'cola'
				},
				{
					label: 'COSE',
					value: 'cose'
				},
				{
					label: 'COSE Bilkent',
					value: 'cose-bilkent'
				},
				{
					label: 'Top to bottom (dagre)',
					value: 'dagre'
				},
				{
					label: 'Left to right (klay)',
					value: 'klay'
				}
			]
		};
		
		this.makeSelectDropdown(graphLayoutSelect,$controls);
		
		let controlsDesc = this.currentView.getControlsSetup();
		let btnParam;
		controlsDesc.forEach((ctrlDesc) => {
			let $ctrl = null;
			let filterOnCtxHandler = null;
			switch(ctrlDesc.type) {
				case 'select':
					$ctrl = this.makeSelectDropdown(ctrlDesc,$controls);
					break;
				case 'slider':
					$ctrl = this.makeSlider(ctrlDesc,$controls);
					
					// Should we generate a context handler for this control?
					if(ctrlDesc.filterOnCtx) {
						filterOnCtxHandler = function(ele) {
							$ctrl.data('slider').setValue(ele.data(ctrlDesc.attr).toFixed(1));
							$ctrl.trigger('slideStop');
						};
					}
					break;
				case 'checkbox':
					$ctrl = this.makeCheckbox(ctrlDesc,$controls);
					break;
				case 'button-group':
					btnParam = $ctrl = $('<div class="param"></div>');
					$controls.append(btnParam);
					break;
				case 'button':
					if(btnParam === undefined) {
						btnParam = $('<div class="param"></div>');
						$controls.append(btnParam);
					}
					$ctrl = this.makeButton(ctrlDesc,btnParam);
					break;
				case 'legend':
					$ctrl = this.makeLegend(ctrlDesc);
					break;
			}
			
			// Could the control be created?
			if($ctrl) {
				// Now, register whether it filters
				if(ctrlDesc.filter in this.filtersDesc) {
					this.filtersDesc[ctrlDesc.filter].push(ctrlDesc);
					
					if(filterOnCtxHandler) {
						this.ctxHandlers[ctrlDesc.filter].push(filterOnCtxHandler);
					}
				}
			} else {
				console.error('ASSERTION on component creation!');
			}
		});
		
		// Static tooltip view
		$controls.append('<span class="label label-default">Selected element</span>');
		this.ui.$tooltipView = $('<div class="tooltip-view"><i>(None)</i></div>');
		$controls.append(this.ui.$tooltipView);
		
		// The next view setup is only set when it is needed
		this.nextViewSetup = this.currentView.getNextViewSetup();
		
		if(this.nextViewSetup) {
			this.makeSelectedNodesView(this.nextViewSetup);
		} else {
			this.hPanel = null;
		}
	}
	
	onSelectHandler(evt,forceUpdate=false) {
		// jshint unused:false
		if(!this.disableHighlightUpdates) {
			let selected = this.cy.nodes('node:selected');
			let selectedEdges = this.cy.edges('edge:selected');
			if(selectedEdges.nonempty()) {
				let connectedEdgesNodes = selectedEdges.connectedNodes();
				if(connectedEdgesNodes.nonempty()) {
					connectedEdgesNodes.select();
					selected.merge(connectedEdgesNodes);
				}
				selectedEdges.unselect();
			}
			
			this.ui.$unselectAll.prop('disabled',selected.empty());
			
			// Re-highlight in case it makes sense
			if(forceUpdate || ((!this.prevHighlighted || this.prevHighlighted.empty()) && selected.nonempty()) || (this.prevHighlighted && selected.symmetricDifference(this.prevHighlighted).nonempty())) {
				this.highlight(selected);
				//if(selected.length===2) {
				//	this.ui.$modal.find('.modal-title').empty().append('Hola holita');
				//	this.ui.$modal.modal('show');
				//}
			}
			
			// Update the title
			var title = this.params.title+(selected.nonempty() ? ' (focused on '+selected.length+')':'');
			
			this.ui.$graphTitle.html(title);
		}
	}
	
	unselectAll() {
		this.cy.elements().unselect();
	}
	
	addSelectionByNodeId(nodeId) {
		// Only select when it was not previously discarded by filtering conditions
		let nodeIds = (nodeId instanceof Array) ? nodeId : [ nodeId ];
		let filteredNodeIds = nodeIds.filter((nId) => this.filteredEles.getElementById(nId).empty());
		if(filteredNodeIds.length > 0) {
			this.batch(() => {
				if(this.unHighlighted) {
					this.unHighlighted.restore();
					this.unHighlighted = null;
				}
				console.log(filteredNodeIds);
				let col = this.cy.collection();
				filteredNodeIds.forEach((nId) => {
					col.merge(this.cy.getElementById(nId));
					console.log(col);
				});
				col.select();
			});
		}
	}
	
	populateNodeTooltip(node) {
		if(!node.scratch('tooltip')) {
			let content = this.currentView.makeNodeTooltipContent(node);
			let ref = node.popperRef(); // used only for positioning
			let nodetip = tippy(ref, { // tippy options:
				content: content,
				trigger: 'manual',
				arrow: true,
				arrowType: 'round',
				placement: 'bottom',
				animation: 'perspective',
				interactive: true,
				interactiveBorder: 5,
				hideOnClick: false,
				multiple: true,
				sticky: true,
				size: 'large',
				theme: 'light',
				zIndex: 999
			});
			node.scratch('tippy',nodetip);
			node.scratch('tooltip',$(content).clone());
		}
		
		return node;
	}
	
	cachedNodeTooltip(node) {
		return this.populateNodeTooltip(node).scratch('tooltip');
	}
	
	cachedNodeTippy(node) {
		return this.populateNodeTooltip(node).scratch('tippy');
	}
	
	populateEdgeTooltip(edge) {
		if(!edge.scratch('tooltip')) {
			let content = this.currentView.makeEdgeTooltipContent(edge);
			let ref = edge.popperRef(); // used only for positioning
			let edgetip = tippy(ref, { // tippy options:
				content: content,
				trigger: 'manual',
				arrow: true,
				arrowType: 'round',
				placement: 'bottom',
				animation: 'perspective',
				//followCursor: true,
				hideOnClick: false,
				multiple: true,
				sticky: true,
				theme: 'dark',
				zIndex: 999
			});
			edge.scratch('tippy',edgetip);
			edge.scratch('tooltip',$(content).clone());
		}
		
		return edge;
	}
	
	cachedEdgeTooltip(edge) {
		return this.populateEdgeTooltip(edge).scratch('tooltip');
	}
	
	cachedEdgeTippy(edge) {
		return this.populateEdgeTooltip(edge).scratch('tippy');
	}
	
	doLayout() {
		// First, empty the container
		this.ui.$graph.empty();
		this.ui.bloodhound.clear();
		
		// This is the graph data
		let graphData = this.currentView.getFetchedNetwork();
		//let graphData = this.testData;
		
		// We feed now the Bloodhound
		this.ui.bloodhound.add(graphData.nodes);
		
		// Registering the initial filtering conditions
		this.params = this.getSavedLayoutParams();
		if(!this.params) {
			// The shared params by this instance of cytoscape
			let graphSetup = this.currentView.getGraphSetup();
			
			this.params = {
				// jshint ignore:start
				...graphSetup,
				// jshint ignore:end
				concentric: function( node ){
				  return node.degree();
				},
				levelWidth: function( /* nodes */ ){
				  return 2;
				}
			};
		}
		
		// Creation of the cytoscape instance
		this.makeCy(this.ui.$graph.get(0),this.cyStyle,graphData);
		
		// Initializing the graph controls (and some values)
		this.initializeControls();
		
		// Next two handlers must be applied before any filtering is applied
		// so no node is left behind
		
		// Now, attach event handlers to each node
		let $ctxNodeHandler = this.ctxHandlers.nodes.length > 0 ?
			(evt) => {
				// Filter by this node
				if(evt.originalEvent.ctrlKey) {
					this.ctxHandlers.nodes.forEach((ctxNodeHandler) => ctxNodeHandler(evt.target));
				} else {
					this.ui.$tooltipView.html(this.cachedNodeTooltip(evt.target));
				}
			}
			:
			(evt) => {
				this.ui.$tooltipView.html(this.cachedNodeTooltip(evt.target));
			};
		
		if($ctxNodeHandler) {
			this.cy.on('cxttap','node',(evt) => {
				let node = evt.target;
				if(!node.isParent()) {
					$ctxNodeHandler(evt);
				}
			});
		}
		
		this.cy.on('tapdragover','node',(evt) => {
			let node = evt.target;
			if(!node.isParent()) {
				let nodetip = this.cachedNodeTippy(node);
				
				if(!nodetip.state.isVisible) {
					nodetip.show();
				}
			}
		});
		
		this.cy.on('tapdragout','node',(evt) => {
			let node = evt.target;
			if(!node.isParent()) {
				let nodetip = node.scratch('tippy');
				if(nodetip && nodetip.state.isVisible) {
					nodetip.hide();
				}
			}
		});
		
		// Now, attach event handlers to each edge
		try {
			let $ctxEdgeHandler = this.ctxHandlers.edges.length > 0 ?
				(evt) => {
					// Filter by this edge
					if(evt.originalEvent.ctrlKey) {
						this.ctxHandlers.edges.forEach((ctxEdgeHandler) => ctxEdgeHandler(evt.target));
					} else {
						this.ui.$tooltipView.html(evt.target.scratch('tooltip'));
					}
				}
				:
				(evt) => {
					this.ui.$tooltipView.html(evt.target.scratch('tooltip'));
				};
			
			if($ctxEdgeHandler) {
				this.cy.on('cxttap','edge',(evt) => {
					$ctxNodeHandler(evt);
				});
			}
			
			this.cy.on('tapdragover','edge',(evt) => {
				let edge = evt.target;
				let edgetip = this.cachedEdgeTippy(edge);
				
				if(!edgetip.state.isVisible) {
					edge.flashClass('highlighted');
					edge.connectedNodes().flashClass('highlighted');
					edgetip.show();
				}
			});
			
			this.cy.on('tapdragout','edge',(evt) => {
				let edge = evt.target;
				let edgetip = edge.scratch('tippy');
				if(edgetip && edgetip.state.isVisible) {
					edgetip.hide();
				}
			});
			
			this.cy.on('select unselect', this.onSelectHandler.bind(this));
		} catch(e) {
			console.log('Unexpected error',e);
		}
		
		// Initializing the graph view (filtering)
		this.cy.batch(() => this.filterOnConditions());
		
		// Creation of the layout, setting the initial parameters
		this.makeLayout();
		
		// Now, the hooks to the different interfaces
		this.running = false;
		
		// First time the layout is run
		this.layout.run();
	}
	
	batch(fn) {
		if(this.cy && fn) {
			this.cy.batch(fn);
		}
	}
	
	fetch() {
		let fetchPromises = [];
		
		if(this.cyStyle === undefined) {
			fetchPromises.push(
				fetch('json/naive-cy-style.json', {mode: 'no-cors'})
				.then((res) => {
					return res.json();
				})
				.then((cyStyle) => {
					this.cyStyle = cyStyle;
					return this.cyStyle;
				})
			);
			//fetchPromises.push(
			//	fetch('json/data.json', {mode: 'no-cors'})
			//	.then((res) => {
			//		return res.json();
			//	})
			//	.then((testData) => {
			//		this.testData = testData;
			//		return this.testData;
			//	})
			//);
		}
		
		return fetchPromises;
	}
}
