'use strict';

import 'bootstrap/dist/css/bootstrap.css';
import 'bootstrap/dist/css/bootstrap-theme.css';
import 'bootstrap-slider/dist/css/bootstrap-slider.css';
import '@fortawesome/fontawesome-free';
import '@fortawesome/fontawesome-free/css/all.css';
import 'tippy.js/dist/tippy.css';
import 'tippy.js/dist/themes/light.css';
import './styles/style.css';

import $ from 'jquery';

import { ComorbiditiesBrowser } from './comorbidities_browser';

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
