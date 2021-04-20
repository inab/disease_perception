const path = require('path');
const webpack = require('webpack');
const CopyWebpackPlugin = require('copy-webpack-plugin');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const ESLintPlugin = require('eslint-webpack-plugin');

const PATHS = {
	app: path.resolve(__dirname,'app'),
	dist: path.resolve(__dirname,'..','REST','static')
};

function escapeRegExpString(str) { return str.replace(/[\-\[\]\/\{\}\(\)\*\+\?\.\\\^\$\|]/g, "\\$&"); }
function pathToRegExp(p) { return new RegExp("^" + escapeRegExpString(p)); }

module.exports = {
	mode: 'development',
	entry: {
		path: path.join(PATHS.app, 'code.js')
	},
	output: {
		filename: 'bundle.js',
		path: PATHS.dist
	},
	plugins:[
		new ESLintPlugin({
			files: PATHS.app
		}),
		new webpack.ProvidePlugin({
			// Parts here are needed to have bootstrap working properly
			$: 'jquery',
			jQuery: 'jquery',
			'window.$': 'jquery',
			'window.jQuery': 'jquery',
			Sammy: ['sammy', 'default' ],
			Popper: ['popper.js', 'default'],
	//		// In case you imported plugins individually, you must also require them here:
	//		//Util: "exports-loader?Util!bootstrap/js/dist/util",
	//		//Dropdown: "exports-loader?Dropdown!bootstrap/js/dist/dropdown",
		}),
		new HtmlWebpackPlugin({
			title: 'BSC Comorbidities web site',
			filename: path.join(PATHS.dist,'index-test.html')
		}),
		new CopyWebpackPlugin([
				{
					context: PATHS.app,
					from: 'json/*.json',
				},
				{
					context: PATHS.app,
					from: 'images/*.svg',
				},
				{
					context: PATHS.app,
					from: 'images/*.png',
				},
				{
					context: PATHS.app,
					from: 'images/*.ico',
				},
				{
					context: PATHS.app,
					from: '*.html',
				}
		])
	],
	module: {
		rules: [
//			{
//				enforce: 'pre',
//				test: /\.js$/,
//				include: pathToRegExp(PATHS.app),
//				loader: "jshint-loader"
//			},
			{
				test: /\.js$/,
				exclude: /(node_modules|bower_components)/,
				use: {
					loader: 'babel-loader',
					options: {
						presets: [
							'@babel/preset-env',
//    							['@babel/preset-stage-2',{'useBuiltIns': true, 'decoratorsLegacy': true}],
						],
						plugins: [
							["module:@babel/plugin-proposal-decorators", { "legacy": true }],
							"module:@babel/plugin-proposal-function-sent",
							"module:@babel/plugin-proposal-export-namespace-from",
							"module:@babel/plugin-proposal-numeric-separator",
							"module:@babel/plugin-proposal-throw-expressions",
						]
					}
				}
			},
			{
				test: /\.css$/,
				loaders: ['style-loader','css-loader']
			},
			{
				test: /\.png$/,
				use: [
					{
						loader: "file-loader",
						options: {
							outputPath: 'images/'
						}
					}
				]
				//loader: "url-loader?prefix=images/&limit=100000"
			},
			{
				test: /\.jpg$/,
				use: [
					{
						loader: "file-loader",
						options: {
							outputPath: 'images/'
						}
					}
				]
				//loader: "file-loader?prefix=images/"
			},
			{
				test: /\.(woff|woff2)(\?v=\d+\.\d+\.\d+)?$/,
				use: [
					{
						loader: "file-loader",
						options: {
							outputPath: 'styles/'
						}
					}
				]
				//loader: 'url-loader?prefix=styles/&limit=10000&mimetype=application/font-woff'
			},
			{
				test: /\.ttf(\?v=\d+\.\d+\.\d+)?$/,
				use: [
					{
						loader: "file-loader",
						options: {
							outputPath: 'styles/'
						}
					}
				]
				//loader: 'url-loader?prefix=styles/&limit=10000&mimetype=application/octet-stream'
			},
			{
				test: /\.eot(\?v=\d+\.\d+\.\d+)?$/,
				use: [
					{
						loader: "file-loader",
						options: {
							outputPath: 'styles/'
						}
					}
				]
				//loader: 'file-loader?prefix=styles/'
			},
			{
				test: /\.svg(\?v=\d+\.\d+\.\d+)?$/,
				use: [
					{
						loader: "file-loader",
						options: {
							outputPath: 'images/'
						}
					}
				]
				//loader: 'url-loader?prefix=images/&limit=10000&mimetype=image/svg+xml'
			}
		]
	}
};
