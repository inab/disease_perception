'use strict';

import 'bootstrap/dist/css/bootstrap.css';
import 'bootstrap/dist/css/bootstrap-theme.css';
import 'bootstrap-slider/dist/css/bootstrap-slider.css';
import 'font-awesome/css/font-awesome.css';
import 'qtip2/dist/jquery.qtip.css';
import './styles/style.css';

import $ from 'jquery';
//var jQuery = require('jquery');
//var $ = jQuery;
//window.$ = $;
//window.jQuery = $;
//window.$ = $;
//window.jQuery = jQuery;

// import 'qtip2';

import _ from 'lodash';
import 'bootstrap';
import 'bootstrap-slider';
import FastClick from 'fastclick';

import cytoscape from 'cytoscape';
import cycola from 'cytoscape-cola';
cytoscape.use( cycola );
//import cyqtip from 'cytoscape-qtip';
//cyqtip( cytoscape, jQuery ); // register extension
import qtip from 'cytoscape-qtip';
cytoscape.use(qtip);
//var qtip = require('cytoscape-qtip');
//cytoscape.use( qtip );

import { Diseases } from './diseases';
import { Patients } from './patients';
import { Genes } from './genes';
import { Drugs } from './drugs';
import { Studies } from './studies';

class ComorbiditiesBrowser {
	constructor(graphEl,configEl,configToggleEl) {
		// The graph container
		this.graphEl = graphEl;
		this.$graph = $(this.graphEl);
		
		// The right panel container
		this.$config = $(configEl);
		// The right panel toggle container
		this.$configToggle = $(configToggleEl);
	}

	initialize() {
		let cyContainer = this.$graph;
		// Preparing the initial data fetch
		let fetchPromises = this.fetch();
		
		this.diseases = new Diseases(cyContainer);
		this.diseases.fetch().forEach((e) => fetchPromises.push(e));
		
		this.patients = new Patients(cyContainer);
		this.patients.fetch().forEach((e) => fetchPromises.push(e));
		
		this.genes = new Genes(cyContainer);
		this.genes.fetch().forEach((e) => fetchPromises.push(e));
		
		this.drugs = new Drugs(cyContainer);
		this.drugs.fetch().forEach((e) => fetchPromises.push(e));
		
		this.studies = new Studies(cyContainer);
		this.studies.fetch().forEach((e) => fetchPromises.push(e));
		
		// Now, issuing the fetch itself, and then the layout
		Promise.all(fetchPromises)
		.then((dataArray) => this.doLayout(dataArray))
		.then(function() {
			FastClick.attach( document.body );
		});
	}
	
	makeCy(container, style, graphData) {
		console.log('UNO',container,style,graphData);
		//window.falla();
		let retval = cytoscape({
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
		
		console.log('DOS');
		
		return retval;
	}
	
	makeLayout(opts) {
		// Should we initialize the shared params?
		if(this.params===undefined) {
			this.params = {
				// jshint ignore:start
				...opts
				// jshint ignore:end
			};
		} else {
			for(let i in opts){
				this.params[i] = opts[i];
			}
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
		$param.append($input);
		
		this.$config.append($param);
		
		let p = $input.slider({
			min: opts.min,
			max: opts.max,
			value: this.params[ opts.param ]
		}).on('slide', _.throttle( () => {
			this.params[ opts.param ] = p.getValue();
			
			this.layout.stop();
			this.makeLayout();
			this.layout.run();
		}, 16 ) ).data('slider');
	}
	
	makeButton(opts) {
		let $button = $('<button class="btn btn-default">'+ opts.label +'</button>');
		
		this.btnParam.append( $button );
		
		$button.on('click', () => {
			this.layout.stop();
			
			if(opts.fn) {
				opts.fn();
			}
			
			this.makeLayout(opts.layoutOpts);
			this.layout.run();
		});
	}
	
	initializeConfigContainer() {
		let $config = this.$config;
		$config.empty();
		
		this.btnParam = $('<div class="param"></div>');
		$config.append( this.btnParam );
		
		let sliders = [
			{
				label: 'Edge length',
				param: 'edgeLengthVal',
				min: 1,
				max: 200
			},
			{
				label: 'Node spacing',
				param: 'nodeSpacing',
				min: 1,
				max: 50
			}
		];
		
		let buttons = [
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
		
		sliders.forEach((slider) => this.makeSlider(slider));
		
		buttons.forEach((button) => this.makeButton(button));
		
		// Event handler to show/hide the config container
		this.$configToggle.on('click', () => {
			$('body').toggleClass('config-closed');
			
			this.cy.resize();
		});
	}
	
	doLayout() {
		// First, empty the container
		this.$graph.empty();
		
		// This is the graph data
		let graphData = this.diseases.getCYComorbiditiesNetwork();
		//let graphData = this.testData;
		
		// The shared params by this instance of cytoscape
		let params = {
			name: 'cola',
			nodeSpacing: 5,
			edgeLengthVal: 45,
			animate: true,
			randomize: false,
			maxSimulationTime: 1500
		};
		
		// Creation of the cytoscape instance
		this.cy = this.makeCy(this.graphEl,this.cyStyle,graphData);
		
		// Creation of the layout, setting the initial parameters
		this.makeLayout(params);
		
		// Now, the hooks to the different interfaces
		this.running = false;
		
		this.cy.on('layoutstart', () => { this.running = true; });
		this.cy.on('layoutstop', () => { this.running = false; });
		
		// Initializing the config panel
		this.initializeConfigContainer();
		
		// First time the layout is run
		this.layout.run();
		
		// Now, attach event handlers to each node
		this.cy.nodes().forEach((n) => {
			let g = n.data('name');
			n.qtip({
				content: [
					{
						name: 'GeneCard',
						url: 'http://www.genecards.org/cgi-bin/carddisp.pl?gene=' + g
					},
					{
						name: 'UniProt search',
						url: 'http://www.uniprot.org/uniprot/?query='+ g +'&fil=organism%3A%22Homo+sapiens+%28Human%29+%5B9606%5D%22&sort=score'
					},
					{
						name: 'GeneMANIA',
						url: 'http://genemania.org/search/human/' + g
					}
				].map(function(link) {
					return '<a target="_blank" href="' + link.url + '">' + link.name + '</a>';
				}).join('<br />\n'),
				position: {
					my: 'top center',
					at: 'bottom center'
				},
				style: {
					classes: 'qtip-bootstrap',
					tip: {
						width: 16,
						height: 8
					}
				}
			});
		});
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
	let configEl = document.getElementById('config');
	let configToggleEl = document.getElementById('config-toggle');

	const browser = new ComorbiditiesBrowser(graphEl,configEl,configToggleEl);
	browser.initialize();
});
