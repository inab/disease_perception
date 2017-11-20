About BSC Comorbidities browser prototype
=========================

The original goal of this project is creating the BSC Comorbidities browser prototype

Installation
------------

1) Install latest stable [NodeJs](http://nodejs.org/) release, either using your operating system / distribution package manager, or by hand.

(If you have installed NodeJs by hand, remember to add its `bin` subdirectory to the `PATH` environment variable)

2) You could also need `ruby` and `gem`.

3) Clone this repository, and run `npm install`, so [Grunt] (http://gruntjs.com/), [Bower] (http://bower.io/) and other dependencies are installed:

```bash
git clone https://github.com/inab/comorbidities.git
npm install
```

4) Add `node_modules/.bin` subdirectory to the `PATH` environment variable, so `bower` and `grunt` can be instantiated

```bash
PATH="${PWD}/node_modules/.bin:${PATH}"
export PATH
```

5) Run `grunt build` in order to prepare and deploy the BSC Comorbidities browser protoype site, which will be deployed at `dist` subdirectory.

```bash
grunt build
```

6) Congratulations! The [DocumentRoot](http://httpd.apache.org/docs/current/mod/core.html#documentroot) of BSC Comorbidities browser protoype is available at the `dist` subdirectory.
