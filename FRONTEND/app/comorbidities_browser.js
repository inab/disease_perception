'use strict';

import $ from 'jquery';

import _ from 'lodash';
import 'bootstrap';
import 'bootstrap-slider';
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
		// The graph container
		this.graphEl = setup.graph;
		this.$graph = $(this.graphEl);
		
		// Create the graph title
		this.$graphTitle = $('<div></div>');
		this.$graphTitle.attr('id','graph-title');
		this.$graphTitle.addClass('graph-title cmui');
		this.$graph.after(this.$graphTitle);
		
		// Create the history and its management buttons
		this.history = [];
		this.historyPointer = -1;
		
		this.$historyBack = $('<button><i class="fa fa-arrow-circle-o-left" aria-hidden="true" title="Previous view"></i></button>');
		this.$historyBack.attr('id','history-back');
		this.$historyBack.addClass('cmui button btn btn-default');
		this.$historyBack.on('click',() => this.historyGoBack());
		this.$historyBack.prop('disabled',true);
		this.$graphTitle.after(this.$historyBack);
		
		this.$unselectAll = $('<button><i class="fa fa-refresh" aria-hidden="true" title="Unselect all"></i></button>');
		this.$unselectAll.attr('id','unselect-all');
		this.$unselectAll.addClass('cmui button btn btn-default');
		this.$unselectAll.on('click',() => this.unselectAll());
		this.$unselectAll.prop('disabled',true);
		this.$historyBack.after(this.$unselectAll);
		
		this.$historyForward = $('<button><i class="fa fa-arrow-circle-o-right" aria-hidden="true" title="Next view"></i></button>');
		this.$historyForward.addClass('cmui button btn btn-default');
		this.$historyForward.attr('id','history-forward');
		this.$historyForward.on('click',() => this.historyGoForward());
		this.$historyForward.prop('disabled',true);
		this.$unselectAll.after(this.$historyForward);
		
		this.$legend = $('<span><i class="fa fa-info-circle" aria-hidden="true"></i></span>');
		this.$legend.addClass('cmui button');
		this.$legend.attr('id','legend');
		this.$legend.hide();
		this.$historyForward.after(this.$legend);
		
		this.$legendBody = $('<div></div>');
		this.$legendBody.addClass('legend-container');
		
		//tippy(this.$legend);
		let tip = tippy.one(this.$legend.get(0),{ // tippy options:
			html: this.$legendBody.get(0),
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
		
		this.$snapshot = $('<a><i class="fa fa-picture-o" aria-hidden="true" title="Save network snapshot"></i></a>');
		this.$snapshot.addClass('cmui button button btn btn-default');
		this.$snapshot.attr('id','snapshot');
		this.$snapshot.on('click',() => this.saveSnapshot());
		this.$legend.after(this.$snapshot);
		
		this.$saveNetwork = $('<a><i class="fa fa-area-chart" aria-hidden="true" title="Save network as Cytoscape.json"></i></a>');
		this.$saveNetwork.addClass('cmui button button btn btn-default');
		this.$saveNetwork.attr('id','save-network');
		this.$saveNetwork.on('click',() => this.saveNetwork());
		this.$snapshot.after(this.$saveNetwork);
		
		
		// The right panel container
		this.$config = $(setup.configPanel);
		// The right panel toggle container
		this.$configToggle = $(setup.configPanelToggle);
		
		this.$controls = $(setup.graphControls);
		
		this.$modal = $(setup.modal);
		this.$loading = $(setup.loading);
		this.$appLoading = $(setup.appLoading);
		
		// Event handler to show/hide the config container
		this.$configToggle.on('click', () => {
			$('body').toggleClass('config-closed');
			
			if(this.cy) {
				this.cy.resize();
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
		this.$loading.removeClass('loaded');
		this.$legend.hide();
		if(historyId===-1) {
			historyId = this.historyPointer;
		} else {
			this.historyPointer = historyId;
		}
		
		this.$historyBack.prop('disabled',this.historyPointer===0);
		this.$historyForward.prop('disabled',this.historyPointer+1 === this.history.length);
		this.$unselectAll.prop('disabled',true);
		
		let viewName = this.history[historyId].viewName;
		let viewParams = this.history[historyId].viewParams;
		
		this.viewName = viewName;
		let currentView = this.currentView = this.views[viewName];
		
		// Preparing the initial data fetch
		let fetchPromises = this.fetch();
		
		currentView.fetch(...viewParams).forEach((e) => fetchPromises.push(e));
		
		// Now, issuing the fetch itself, and then the layout
		Promise.all(fetchPromises)
		.then((dataArray) => {
			this.doLayout(dataArray);
			let selected = this.getSavedSelectedNodes();
			if(selected.nonempty()) {
				selected.select();
			}
			this.$loading.addClass('loaded');
			this.$appLoading.addClass('loaded');
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
	
	saveSnapshot() {
		this.$snapshot.attr('download','disease-perception_'+this.getViewId()+'.png');
		this.$snapshot.attr('href',this.cy.png());
	}
	
	saveNetwork() {
		this.$saveNetwork.attr('download','disease-perception_'+this.getViewId()+'.json');
		this.$saveNetwork.attr('href',urlfy.toDataURL(JSON.stringify(this.cy.json()),'application/json'));
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
		$cont.append('<i class="fa fa-circle" style="vertical-align: text-top; color: '+node.data('color')+';"></i>');
		$option.append($cont);
		
		//$option.append($nodeOption);
		//$option.append('<i class="fa fa-circle" style="color: '+node.data('color')+';"></i>');
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
		this.$config.append($widget);
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
				label: '<i class="fa fa-check-square-o" title="Select all"></i>',
				fn: () => {
					$nodeList.find('input[type="checkbox"]').prop('checked',true);
					this.updateSelectedNodesCount($nodeList.find('input[type="checkbox"]:checked'));
				},
			},$selectedNodesView);
		let $selectNone = this.makeButton({
				classes: 'btn-xs',
				label: '<i class="fa fa-square-o" title="Unselect all"></i>',
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
		this.$legendBody.empty();
		this.$legendBody.append(opts.domNode);
		this.$legend.show();
		
		return this.$legendBody;
	}
	
	initializeControls() {
		let $controls = this.$controls;
		$controls.empty();
		
		if(this.configWidgets.length > 0) {
			this.configWidgets.forEach(function($widget) {
				$widget.remove();
			});
			
			this.configWidgets = [];
		}
		
		// First and foremost, set the title
		this.$graphTitle.html(this.params.title);
		
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
		this.$tooltipView = $('<div class="tooltip-view"><i>(None)</i></div>');
		$controls.append(this.$tooltipView);
		
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
			
			this.$unselectAll.prop('disabled',selected.empty());
			
			// Re-highlight in case it makes sense
			if(forceUpdate || ((!this.prevHighlighted || this.prevHighlighted.empty()) && selected.nonempty()) || (this.prevHighlighted && selected.symmetricDifference(this.prevHighlighted).nonempty())) {
				this.highlight(selected);
				//if(selected.length===2) {
				//	this.$modal.find('.modal-title').empty().append('Hola holita');
				//	this.$modal.modal('show');
				//}
			}
			
			// Update the title
			var title = this.params.title+(selected.nonempty() ? ' (focused on '+selected.length+')':'');
			
			this.$graphTitle.html(title);
		}
	}
	
	unselectAll() {
		this.cy.elements().unselect();
	}
	
	doLayout() {
		// First, empty the container
		this.$graph.empty();
		
		// This is the graph data
		let graphData = this.currentView.getFetchedNetwork();
		//let graphData = this.testData;
		
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
				levelWidth: function( nodes ){
				  return 2;
				}
			};
		}
		
		// Creation of the cytoscape instance
		this.makeCy(this.graphEl,this.cyStyle,graphData);
		
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
					this.$tooltipView.html(evt.target.scratch('tooltip'));
				}
			}
			:
			(evt) => {
				this.$tooltipView.html(evt.target.scratch('tooltip'));
			};
		
		this.cy.nodes().forEach((node) => {
			if(!node.isParent()) {
				let ref = node.popperRef(); // used only for positioning

				// using tippy ^2.0.0
				let content = this.currentView.makeNodeTooltipContent(node);
				node.scratch('tooltip',$(content).clone());
				let tip = tippy(ref, { // tippy options:
					html: content,
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
				}).tooltips[0];
				
				node.on('tapdragover', () => {
					if(!tip.state.visible) {
						tip.show();
					}
				});
				
				node.on('tapdragout', () => {
					if(tip.state.visible) {
						tip.hide();
					}
				});
				
				if($ctxNodeHandler) {
					node.on('cxttap',$ctxNodeHandler);
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
						this.$tooltipView.html(evt.target.scratch('tooltip'));
					}
				}
				:
				(evt) => {
					this.$tooltipView.html(evt.target.scratch('tooltip'));
				};
			
			this.cy.edges().forEach((edge) => {
				let ref = edge.popperRef(); // used only for positioning

				// using tippy ^2.0.0
				let content = this.currentView.makeEdgeTooltipContent(edge);
				edge.scratch('tooltip',$(content).clone());
				let tip = tippy(ref, { // tippy options:
					html: content,
					trigger: 'manual',
					arrow: true,
					arrowType: 'round',
					placement: 'bottom',
					animation: 'perspective',
					followCursor: true,
					multiple: false,
					sticky: true,
					theme: 'dark',
					zIndex: 999
				}).tooltips[0];
				
				edge.on('tapdragover', (e) => {
					//if(!tip.state.visible && (this.unHighlighted || e.originalEvent.ctrlKey)) {
					if(!tip.state.visible) {
						edge.flashClass('highlighted');
						edge.connectedNodes().flashClass('highlighted');
						tip.show();
					}
				});
				
				edge.on('tapdragout', () => {
					if(tip.state.visible) {
						tip.hide();
					}
				});
				
				if($ctxEdgeHandler) {
					edge.on('cxttap',$ctxEdgeHandler);
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
