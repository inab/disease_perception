'use strict';

import 'bootstrap/dist/css/bootstrap.css';
import 'bootstrap/dist/css/bootstrap-theme.css';
import 'bootstrap-slider/dist/css/bootstrap-slider.css';
import 'font-awesome/css/font-awesome.css';
import 'tippy.js/dist/tippy.css';
import 'tippy.js/dist/themes/light.css';
import './styles/style.css';

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

// Internal code
import { Diseases } from './diseases';
import { Patients } from './patients';
import { PatientSubgroups } from './patient_subgroups';
import { Genes } from './genes';
import { Drugs } from './drugs';
import { Studies } from './studies';


function sleep(millis) {
	return new Promise((resolve) => setTimeout(resolve,millis));
}

class ComorbiditiesBrowser {
	constructor(setup) {
		// The graph container
		this.graphEl = setup.graph;
		this.$graph = $(this.graphEl);
		
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
		
		this.viewName = viewName;
		let currentView = this.currentView = this.views[viewName];
		
		// Preparing the initial data fetch
		let fetchPromises = this.fetch();
		
		currentView.fetch(...viewParams).forEach((e) => fetchPromises.push(e));
		
		// Now, issuing the fetch itself, and then the layout
		this.$loading.removeClass('loaded');
		Promise.all(fetchPromises)
		.then((dataArray) => {
			this.$loading.addClass('loaded');
			this.$appLoading.addClass('loaded');
			this.doLayout(dataArray);
		});
	}
	
	makeCy(container, style, graphData) {
		if(this.cy) {
			this.layout.stop();
			this.layout.destroy();
			this.layout = null;
			this.unHighlighted = null;
			this.prevHighlighted = null;
			this.hiddenNodes = null;
			this.hiddenArcs = null;
			this.cy.destroy();
			this.cy = null;
		}
		
		this.cy = cytoscape({
			container: container,
			//style: style,
			style: [
			//	// jshint ignore:start
			//	...graphData.style,
				...style
			//	// jshint ignore:end
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
	
		
	makeSlider(opts) {
		let $input = $('<input></input>');
		let $param = $('<div class="param"></div>');
		
		$param.append('<span class="label label-default">'+ opts.label +'</span>');
		
		let initialValue = Math.round(this.params[ opts.param ]);
		let $dataLabel = $('<span class="label label-info">'+ initialValue +'</span>');
		$param.append($dataLabel);
		$param.append($input);
				
		let scale = opts.scale === undefined ? 'linear' : opts.scale;
		
		let p = $input.slider({
			min: Math.floor(opts.min),
			max: Math.ceil(opts.max),
			scale: scale,
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
		
		return $param;
	}
	
	makeButton(opts,btnParam) {
		if(btnParam === undefined) {
			btnParam = this.btnParam;
		}
		
		let optsLabel = opts.label ? opts.label : opts.value;
		let $button = $('<button type="button" class="btn btn-default">' + optsLabel + '</button>');
		
		if(opts.value) {
			$button.val(opts.value);
		}
		
		$button.on('click', () => {
			if(opts.param) {
				this.params[ opts.param ] = $button.val();
			}
			
			this.layout.stop();
			
			if(opts.fn) {
				opts.fn();
			}
			
			this.makeLayout(opts.layoutOpts);
			this.layout.run();
		});
		
		btnParam.append( $button );
	}
	
	makeSelectButtons(opts,btnParam) {
		if(btnParam === undefined) {
			btnParam = this.btnParam;
		}
		
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
	}
	
	makeSelectDropdown(opts,btnParam) {
		if(btnParam === undefined) {
			btnParam = this.btnParam;
		}

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
	}
	
	makeNodeOption(node,isInitiallyChecked,opts) {
		let $option = $('<div></div>');
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
		
		$option.append($nodeOption);
		$option.append('<i class="fa fa-circle" style="color: '+node.data('color')+';"></i>');
		$option.append(node.data('name'));
		return $option;
	}
	
	updateSelectedNodesCount(nodes) {
		if(this.hPanel) {
			let hPanel = this.hPanel;
			hPanel.$nodeListLabel.html(nodes.length);
			hPanel.$nodeListNextViewButton.prop('disabled', nodes.length < 2);
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
		
		let $nodeListNextViewButton = hPanel.$nodeListNextViewButton = $('<input type="button" class="btn btn-default btn-xs" value="'+opts.nextLabel+'" />');
		$nodeListNextViewButton.on('click',() => {
			let nextViewIds = hPanel.$nodeList.find('input[type="checkbox"]:checked').toArray().map((check) => {
				let checkbox = $(check);
				
				return checkbox.data(opts.idPropertyName);
			});
			this.switchView('patient_subgroups',nextViewIds);
		});
		
		$selectedNodesView.append($nodeListNextViewButton);
		
		this.registerConfigWidget($selectedNodesView);
		
		// The container of the selected nodes
		let $nodeList = hPanel.$nodeList = $('<div style="overflow-y:auto;max-height: 25%;background-color:white;color:black;"></div>');
		$nodeList.data('opts',opts);
		$nodeList.hide();
		
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
				
				hPanel.$nodeListLabel.empty();
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


	filterEdgesOnAbsRisk() {
		if(this.prevHighlighted && this.prevHighlighted.nonempty()) {
			this.unHighlighted.restore();
			this.unHighlighted = null;
		}
		
		if(this.hiddenNodes) {
			this.hiddenNodes.restore();
		}
		
		if(this.hiddenArcs) {
			this.hiddenArcs.restore();
		}
		
		// Applying the initial filtering
		this.hiddenArcs = this.cy.edges((e) => {
			return e.data('abs_rel_risk') < this.params.absRelRiskVal;
		}).remove();
		
		// Now, remove the orphaned nodes
		this.hiddenNodes = this.cy.nodes((n) => {
			return !n.isParent() && (n.degree(true) === 0);
			//return n.degree(true) === 0;
		}).remove();
		
		// And, at last, highlight again
		if(this.prevHighlighted && this.prevHighlighted.nonempty()) {
			this.highlight(this.prevHighlighted);
		}
	}
	
	// This method is not working as expected, so disable it for now
	toggleDiseaseGroups() {
		if(this.hiddenDiseaseGroups) {
			this.hiddenDiseaseGroups.restore();
			this.hiddenDiseaseGroups = null;
		} else {
			// There could be disease groups in hidden nodes
			if(this.hiddenNodes) {
				this.hiddenNodes.restore();
				this.hiddenNodes = null;
			}
			
			this.hiddenDiseaseGroups = this.cy.nodes((n) => {
				return n.isParent();
			}).remove();
			this.hiddenDiseaseGroups.filter((n) => { return !n.isParent(); }).restore();
		}
		
		this.filterEdgesOnAbsRisk();
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
		
		let absRelRiskData = this.currentView.getAbsRelRiskRange();
		
		let sliders = [
			{
				label: 'Cut-off on |Relative risk|',
				param: 'absRelRiskVal',
				min: absRelRiskData.min,
				max: absRelRiskData.max,
				scale: 'logarithmic',
				fn: () => this.cy.batch(() => this.filterEdgesOnAbsRisk())
			},
			//{
			//	label: 'Edge length',
			//	param: 'edgeLengthVal',
			//	min: 1,
			//	max: 200
			//},
			{
				label: 'Node spacing',
				param: 'nodeSpacing',
				min: 1,
				max: 50
			}
		];
		
		let buttons = [
			//{
			//	label: '<i class="fa fa-object-group"></i>',
			//	layoutOpts: {
			//		randomize: true
			//	},
			//	fn: () => this.toggleDiseaseGroups()
			//},
			//{
			//	label: '<i class="fa fa-object-ungroup"></i>',
			//	layoutOpts: {
			//		randomize: true
			//	},
			//	fn: () => this.toggleDiseaseGroups()
			//},
			{
				label: '<i class="fa fa-random"></i>',
				layoutOpts: {
					randomize: true,
					flow: null
				}
			},
			{
				label: '<i class="fa fa-long-arrow-down"></i>',
				layoutOpts: {
					flow: {
						axis: 'y',
						minSeparation: 30
					}
				}
			}
		];
		
		let selects = [
			{
				label: 'Graph Layouts',
				param: 'name',
				options: [
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
						label: 'Dagre (slow)',
						value: 'dagre'
					},
					{
						label: 'Klay (slow)',
						value: 'klay'
					}
				]
			}
		];
		
		selects.forEach((select) => this.makeSelectDropdown(select,this.$controls));
		
		sliders.forEach((slider) => {
			let $slider = this.makeSlider(slider);
			this.$controls.append($slider);
		});
		
		this.btnParam = $('<div class="param"></div>');
		$controls.append( this.btnParam );
		
		buttons.forEach((button) => this.makeButton(button));
		
		// The next view setup is only set when it is needed
		let nextViewSetup = this.currentView.getNextViewSetup();
		
		if(nextViewSetup) {
			this.makeSelectedNodesView(nextViewSetup);
		} else {
			this.hPanel = null;
		}
	}
	
	doLayout() {
		// First, empty the container
		this.$graph.empty();
		
		// This is the graph data
		let graphData = this.currentView.getFetchedNetwork();
		//let graphData = this.testData;
		
		// The shared params by this instance of cytoscape
		let graphSetup = this.currentView.getGraphSetup();
		
		// Creation of the cytoscape instance
		this.makeCy(this.graphEl,this.cyStyle,graphData);
		
		// Next two handlers must be applied before any filtering is applied
		// so no node is left behind
		
		// Now, attach event handlers to each node
		this.cy.nodes().forEach((node) => {
			if(!node.isParent()) {
				let ref = node.popperRef(); // used only for positioning

				// using tippy ^2.0.0
				let tip = tippy(ref, { // tippy options:
					html: this.currentView.makeNodeTooltipContent(node),
					trigger: 'manual',
					arrow: true,
					arrowType: 'round',
					placement: 'bottom',
					animation: 'perspective',
					interactive: true,
					interactiveBorder: 5,
					delay: 2000,
					hideOnClick: false,
					multiple: true,
					sticky: true,
					size: 'large',
					theme: 'light',
					zIndex: 999
				}).tooltips[0];
				
				node.on('tapdragover', () => {
					tip.show();
				});
				
				node.on('tapdragout', () => {
					tip.hide();
				});
			}
		});
		
		// Now, attach event handlers to each edge
		try {
			this.cy.edges().forEach((edge) => {
				let ref = edge.popperRef(); // used only for positioning

				// using tippy ^2.0.0
				let tip = tippy(ref, { // tippy options:
					html: this.currentView.makeEdgeTooltipContent(edge),
					trigger: 'manual',
					arrow: true,
					arrowType: 'round',
					placement: 'bottom',
					animation: 'perspective',
					delay: 2000,
					multiple: true,
					sticky: true,
					theme: 'dark',
					zIndex: 999
				}).tooltips[0];
				
				edge.on('tapstart', () => {
					tip.show();
				});
			});
			
			this.cy.on('select unselect', () => {
				let selected = this.cy.elements('node:selected');
				if(!this.prevHighlighted || selected.symmetricDifference(this.prevHighlighted).nonempty()) {
					this.highlight(selected);
					//if(selected.length===2) {
					//	this.$modal.find('.modal-title').empty().append('Hola holita');
					//	this.$modal.modal('show');
					//}
				}
			});
		} catch(e) {
			console.log('Unexpected error',e);
		}
		
		// Applying the initial filtering
		this.params = {
			// jshint ignore:start
			...graphSetup
			// jshint ignore:end
		};
		this.cy.batch(() => this.filterEdgesOnAbsRisk());
		
		// Creation of the layout, setting the initial parameters
		this.makeLayout();
		
		// Now, the hooks to the different interfaces
		this.running = false;
		
		// Initializing the graph controls
		this.initializeControls();
		
		// First time the layout is run
		this.layout.run();
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

$(document).ready(function() {
	let graphEl = document.getElementById('graph');
	let configToggleEl = document.getElementById('config-toggle');
	let configEl = document.getElementById('config');
	let modalEl = document.getElementById('modalGraphChange');
	let appLoadingEl = document.getElementById('comorbidities-loading');
	let graphLoadingEl = document.getElementById('graph-loading');
	let graphControlsEl = document.getElementById('graph-controls');

	const browser = new ComorbiditiesBrowser({
		'graph': graphEl,
		'configPanel': configEl,
		'configPanelToggle': configToggleEl,
		'graphControls': graphControlsEl,
		'modal': modalEl,
		'appLoading': appLoadingEl,
		'loading': graphLoadingEl
	});
	
	browser.switchView('diseases');
});
