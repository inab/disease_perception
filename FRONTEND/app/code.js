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

Promise.all([
  fetch('json/cy-style.json', {mode: 'no-cors'})
    .then(function(res) {
      return res.json();
    }),
  fetch('json/data.json', {mode: 'no-cors'})
    .then(function(res) {
      return res.json();
    }),
  fetch('api/diseases', {mode: 'no-cors'})
    .then(function(res) {
      return res.json();
    }),
  fetch('api/diseases/groups', {mode: 'no-cors'})
    .then(function(res) {
      return res.json();
    }),
  fetch('api/patients', {mode: 'no-cors'})
    .then(function(res) {
      return res.json();
    }),
  fetch('api/patients/subgroups', {mode: 'no-cors'})
    .then(function(res) {
      return res.json();
    }),
  fetch('api/drugs', {mode: 'no-cors'})
    .then(function(res) {
      return res.json();
    }),
  fetch('api/genes', {mode: 'no-cors'})
    .then(function(res) {
      return res.json();
    }),
  fetch('api/studies', {mode: 'no-cors'})
    .then(function(res) {
      return res.json();
    }),
])
  .then(function(dataArray) {
    var cy = window.cy = cytoscape({
      container: document.getElementById('cy'),
      style: dataArray[0],
      elements: dataArray[1]
    });

    var params = {
      name: 'cola',
      nodeSpacing: 5,
      edgeLengthVal: 45,
      animate: true,
      randomize: false,
      maxSimulationTime: 1500
    };

    function makeLayout( opts ){
      params.randomize = false;
      params.edgeLength = function(e){ return params.edgeLengthVal / e.data('weight'); };

      for( var i in opts ){
        params[i] = opts[i];
      }

      return cy.layout( params );
    }

    var layout = makeLayout();
    var $config = $('#config');
    var $btnParam = $('<div class="param"></div>');
    $config.append( $btnParam );

    function makeSlider( opts ){
      var $input = $('<input></input>');
      var $param = $('<div class="param"></div>');

      $param.append('<span class="label label-default">'+ opts.label +'</span>');
      $param.append( $input );

      $config.append( $param );

      var p = $input.slider({
        min: opts.min,
        max: opts.max,
        value: params[ opts.param ]
      }).on('slide', _.throttle( function(){
        params[ opts.param ] = p.getValue();

        layout.stop();
        layout = makeLayout();
        layout.run();
      }, 16 ) ).data('slider');
    }

    function makeButton( opts ){
      var $button = $('<button class="btn btn-default">'+ opts.label +'</button>');

      $btnParam.append( $button );

      $button.on('click', function(){
        layout.stop();

        if( opts.fn ){ opts.fn(); }

        layout = makeLayout( opts.layoutOpts );
        layout.run();
      });
    }

    var running = false;

    cy.on('layoutstart', function(){
      running = true;
    }).on('layoutstop', function(){
      running = false;
    });

    layout.run();


    var sliders = [
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

    var buttons = [
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
          flow: { axis: 'y', minSeparation: 30 }
        }
      }
    ];

    sliders.forEach( makeSlider );

    buttons.forEach( makeButton );
	
    cy.nodes().forEach(function(n){
      var g = n.data('name');
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
        ].map(function( link ){
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

    $('#config-toggle').on('click', function(){
      $('body').toggleClass('config-closed');

      cy.resize();
    });

  })
  .then(function() {
    FastClick.attach( document.body );
});
