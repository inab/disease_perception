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
		if(this.cy) {
			this.cy.destroy();
			this.cy = null;
			this.layout = null;
			this.hiddenNodes = null;
			this.hiddenArcs = null;
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
		$param.append($input);
		
		this.$config.append($param);
		
		let scale = opts.scale === undefined ? 'linear' : opts.scale;
		
		let p = $input.slider({
			min: opts.min,
			max: opts.max,
			scale: scale,
			value: this.params[ opts.param ]
		}).on('change', _.throttle( () => {
			this.params[ opts.param ] = p.getValue();
			
			this.layout.stop();
			
			if(opts.fn) {
				opts.fn();
			}
			
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
	
	filterEdgesOnAbsRisk() {
		if(this.hiddenNodes) {
			this.hiddenNodes.restore();
		}
		
		if(this.hiddenArcs) {
			this.hiddenArcs.restore();
		}
		
		// Applying the initial filtering
		this.hiddenArcs = this.cy.edges((e) => {
			return Math.abs(e.data('rel_risk')) < this.params.absRelRiskVal;
		}).remove();
		
		// And now, remove the orphaned nodes
		this.hiddenNodes = this.cy.nodes((n) => {
			return !n.isParent() && (n.degree(true) === 0);
			//return n.degree(true) === 0;
		}).remove();
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
	
	initializeConfigContainer() {
		let $config = this.$config;
		$config.empty();
		
		this.btnParam = $('<div class="param"></div>');
		$config.append( this.btnParam );
		
		let absRelRiskData = this.diseases.getAbsRelRiskRange();
		
		let sliders = [
			{
				label: 'Cut-off on |Relative risk|',
				param: 'absRelRiskVal',
				min: absRelRiskData.min,
				max: absRelRiskData.max,
				scale: 'logarithmic',
				fn: () => this.filterEdgesOnAbsRisk()
			},
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
		
		sliders.forEach((slider) => this.makeSlider(slider));
		
		buttons.forEach((button) => this.makeButton(button));
		
		// Event handler to show/hide the config container
		this.$configToggle.on('click', () => {
			$('body').toggleClass('config-closed');
			
			if(this.cy) {
				this.cy.resize();
			}
		});
	}
	
	doLayout() {
		// First, empty the container
		this.$graph.empty();
		
		// This is the graph data
		let graphData = this.diseases.getCYComorbiditiesNetwork();
		//let graphData = this.testData;
		
		// The shared params by this instance of cytoscape
		let absRelRiskData = this.diseases.getAbsRelRiskRange();
		console.log(absRelRiskData);
		
		let params = {
			name: 'cola',
			nodeSpacing: 5,
			edgeLengthVal: 45,
			absRelRiskVal: absRelRiskData.initial,
			animate: true,
			randomize: false,
			maxSimulationTime: 1500
		};
		
		// Creation of the cytoscape instance
		this.makeCy(this.graphEl,this.cyStyle,graphData);
		
		// Applying the initial filtering
		this.params = params;
		this.filterEdgesOnAbsRisk();
		
		// Creation of the layout, setting the initial parameters
		this.makeLayout();
		
		// Now, the hooks to the different interfaces
		this.running = false;
		
		// Initializing the config panel
		this.initializeConfigContainer();
		
		// First time the layout is run
		this.layout.run();
		
		// Now, attach event handlers to each node
		this.cy.nodes().forEach((n) => {
			let diseaseName = n.data('name');
			let diseaseLower = diseaseName.replace(/ +/g,'-').toLowerCase();
			let icd9 = n.data('icd9');
			let icd10 = n.data('icd10');
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
			
			if(icd10!=='-') {
				links.push({
					name: 'ICDList',
					url: 'https://icdlist.com/icd-10/' + encodeURIComponent(icd10)
				});
			}
			
			n.qtip({
				content: '<b>'+diseaseName+'</b><br />\n'+
				'ICD9: '+icd9 + ' ICD10: ' + icd10 + '<br />\n' +
					links.map(function(link) {
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
