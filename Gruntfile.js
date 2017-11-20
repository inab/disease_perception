'use strict';

module.exports = function (grunt) {
	// Load grunt tasks automatically
	require('load-grunt-tasks')(grunt);
	
	// Time how long tasks take. Can help when optimizing build times
	require('time-grunt')(grunt);
	
	var bowerConfig = require('./bower.json');
	// Configurable paths for the application
	var appConfig = {
		app: bowerConfig.appPath || 'app',
		dist: 'dist'
	};
	
	var debug = true;
	
	var useminPrepare;
	var buildTasks;
	var buildTasksFast;
	if(debug) {
		useminPrepare = {
			html: '<%= yeoman.app %>/*.html',
			options: {
				dest: '<%= yeoman.dist %>',
				flow: {
					html: {
						steps: {
							// js: ['concat', 'uglifyjs'],
							// css: ['cssmin']
							js: ['concat'],
							css: ['concat']
						},
						post: {}
					}
				}
			}
		};
		
		buildTasks = [
			'clean:dist',
			'bower-update',
			'wiredep',
			'copy:styles',
			'useminPrepare',
			'concurrent:dist',
			'autoprefixer',
			'concat',
			'copy:dist',
			//'cssmin',
			//'uglify',
			'filerev',
			'usemin',
			//'htmlmin'
		];
		buildTasksFast = [
			//'clean:dist',
			//'bower-update',
			'wiredep',
			'copy:styles',
			'useminPrepare',
			'concurrent:dist',
			'autoprefixer',
			'concat',
			'copy:dist',
			//'cssmin',
			//'uglify',
			'filerev',
			'usemin',
			//'htmlmin'
		];
	} else {
		useminPrepare = {
			html: '<%= yeoman.app %>/*.html',
			options: {
				dest: '<%= yeoman.dist %>',
				flow: {
					html: {
						steps: {
							js: ['concat', 'uglifyjs'],
							css: ['cssmin']
						},
						post: {}
					}
				}
			}
		};
		buildTasks = [
			'clean:dist',
			'bower-update',
			'wiredep',
			'copy:styles',
			'useminPrepare',
			'concurrent:dist',
			'autoprefixer',
			'concat',
			'copy:dist',
			'cssmin',
			'uglify',
			'filerev',
			'usemin',
			'htmlmin'
		];
		buildTasksFast = [
			'clean:dist',
			//'bower-update',
			'wiredep',
			'copy:styles',
			'useminPrepare',
			'concurrent:dist',
			'autoprefixer',
			'concat',
			'copy:dist',
			'cssmin',
			'uglify',
			'filerev',
			'usemin',
			'htmlmin'
		];
	}
	
	// Define the configuration for all the tasks
	grunt.initConfig({
		// Project settings
		yeoman: appConfig,
	
    // Make sure code styles are up to par and there are no obvious mistakes
    jshint: {
      options: {
        jshintrc: '.jshintrc',
        reporter: require('jshint-stylish')
      },
      all: {
        src: [
          'Gruntfile.js',
          '<%= yeoman.app %>/scripts/{,*/}*.js'
        ]
      },
      test: {
        options: {
          jshintrc: 'test/.jshintrc'
        },
        src: ['test/spec/{,*/}*.js']
      }
    },

    // Empties folders to start fresh
    clean: {
      dist: {
        files: [{
          dot: true,
          src: [
            '.tmp',
            '<%= yeoman.dist %>/{,*/}*',
            '!<%= yeoman.dist %>/.git*'
          ]
        }]
      },
      server: '.tmp'
    },

    // Add vendor prefixed styles
    autoprefixer: {
      options: {
        browsers: ['last 1 version']
      },
      dist: {
        files: [{
          expand: true,
          cwd: '.tmp/styles/',
          src: '{,*/}*.css',
          dest: '.tmp/styles/'
        }]
      }
    },

    // Automatically inject Bower components into the app
    wiredep: {
      options: {

      },
      app: {
        src: ['<%= yeoman.app %>//*.html'],
        ignorePath:  /\.\.\//
      }
    },

    // Renames files for browser caching purposes
    filerev: {
      dist: {
        src: [
          '<%= yeoman.dist %>/scripts/{,*/}*.js',
          '<%= yeoman.dist %>/styles/{,*/}*.css',
          '<%= yeoman.dist %>/images/{,*/}*.{png,jpg,jpeg,gif,webp,svg}',
          '<%= yeoman.dist %>/styles/fonts/*'
        ]
      }
    },

    // Reads HTML for usemin blocks to enable smart builds that automatically
    // concat, minify and revision files. Creates configurations in memory so
    // additional tasks can operate on them
    useminPrepare: useminPrepare,

    // Performs rewrites based on filerev and the useminPrepare configuration
    usemin: {
      html: ['<%= yeoman.dist %>/{,*/}*.html'],
      css: ['<%= yeoman.dist %>/styles/{,*/}*.css'],
      js: ['<%= yeoman.dist %>/scripts/{,*/}*.js'],
      //options: {
      //  patterns: {
      //    js: [
      //      [/(images\/Chromosome_[^.]+\.svg)/gm, 'Update the JS to reference our SVG images'],
      //      [/(images\/GRCh38_chromosome_[^.]+\.svg)/gm, 'Update the JS to reference our SVG images'],
      //      [/(images\/chr\.svg)/gm, 'Update the JS to reference our SVG images'],
      //    ]
      //  },
      //  assetsDirs: ['<%= yeoman.dist %>','<%= yeoman.dist %>/images']
      //}
    },

    // The following *-min tasks will produce minified files in the dist folder
    // By default, your `index.html`'s <!-- Usemin block --> will take care of
    // minification. These next options are pre-configured if you do not wish
    // to use the Usemin blocks.
    // cssmin: {
    //   dist: {
    //     files: {
    //       '<%= yeoman.dist %>/styles/main.css': [
    //         '.tmp/styles/{,*/}*.css'
    //       ]
    //     }
    //   }
    // },
    // uglify: {
    //   dist: {
    //     files: {
    //       '<%= yeoman.dist %>/scripts/scripts.js': [
    //         '<%= yeoman.dist %>/scripts/scripts.js'
    //       ]
    //     }
    //   }
    // },
    // concat: {
    //   dist: {}
    // },

    imagemin: {
      dist: {
        files: [{
          expand: true,
          cwd: '<%= yeoman.app %>/images',
          src: '{,*/}*.{png,jpg,jpeg,gif}',
          dest: '<%= yeoman.dist %>/images'
        }]
      }
    },

    svgmin: {
      dist: {
        files: [{
          expand: true,
          cwd: '<%= yeoman.app %>/images',
          src: '{,*/}*.svg',
          dest: '<%= yeoman.dist %>/images'
        }]
      }
    },

    htmlmin: {
      dist: {
        options: {
          collapseWhitespace: true,
          conservativeCollapse: true,
          collapseBooleanAttributes: true,
          removeCommentsFromCDATA: true,
          removeOptionalTags: true
        },
        files: [{
          expand: true,
          cwd: '<%= yeoman.dist %>',
          src: ['*.html', 'views/{,*/}*.html'],
          dest: '<%= yeoman.dist %>'
        }]
      }
    },

    // Copies remaining files to places other tasks can use
    copy: {
      dist: {
        files: [{
          expand: true,
          dot: true,
          cwd: '<%= yeoman.app %>',
          dest: '<%= yeoman.dist %>',
          src: [
            '*.{ico,png,txt,svg}',
            '.htaccess',
            '*.html',
            'views/{,*/}*.html',
            'images/{,*/}*.{webp}',
            'scripts/*.json',
            'fonts/*'
          ]
        }, {
          expand: true,
          cwd: '.tmp/images',
          dest: '<%= yeoman.dist %>/images',
          src: ['generated/*']
        }, {
          expand: true,
          cwd: 'node_modules/@bower_components/cartodb.js/dist/themes/img',
          src: '*',
          dest: '<%= yeoman.dist %>/img',
        }, {
          expand: true,
          cwd: 'node_modules/@bower_components/cartodb.js/dist/themes/css/images',
          src: ['*.png','*.gif'],
          dest: '<%= yeoman.dist %>/styles/images',
        }]
      },
      styles: {
        expand: true,
        cwd: '<%= yeoman.app %>/styles',
        dest: '.tmp/styles/',
        src: '*.css'
      }
    },

    // Run some tasks in parallel to speed up the build process
    concurrent: {
      dist: [
        'imagemin',
        'svgmin'
      ]
    },
  });
	
	grunt.registerTask('bower-update', 'install/update bower dependencies', function() {
		var exec = require('child_process').exec;
		var cb = this.async();
		exec('bower update', function(err, stdout/*, stderr*/) {
			console.log(stdout);
			cb();
		});
	});
	
	grunt.registerTask('build', buildTasks);
	grunt.registerTask('build:fast', buildTasksFast);
	
	grunt.registerTask('default', [
		'newer:jshint',
		'test',
		'build'
	]);
};
