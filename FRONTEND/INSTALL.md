# Install instructions of BSC Comorbidities browser

The source code of this browser is written for Javascript ES6. It depends on the libraries declared in [package.json](package.json) file.

* In order to compile the dependencies you need to have installed latest stable [NodeJs](http://nodejs.org/) release, either using your operating system / distribution package manager, or by hand. If you have installed NodeJs by hand, remember to add its `bin` subdirectory to the `PATH` environment variable.

  - Due some intermediate dependencies, you could also need `ruby` and `gem`.
  
* Clone this repository, change to the directory `FRONTEND` and run `npm install yarn`, so [Yarn](https://yarnpkg.com/) installation dependency, which is used to fetch [Webpack](https://webpack.github.io/) and other dependencies are installed:

```bash
git clone https://github.com/inab/comorbidities_frontend.git
cd FRONTEND
npm install --no-save yarn
```

* Add `node_modules/.bin` subdirectory to the `PATH` environment variable, so `yarn` and other installation dependencies can be instantiated. Then, call `yarn`, so the other dependencies are fetched:

```bash
PATH="${PWD}/node_modules/.bin:${PATH}"
export PATH
yarn --frozen-lockfile
```

* Now, you have to run `webpack` in order to prepare and deploy the BSC Comorbidities browser site, which will be deployed at `../REST/static` subdirectory.

```bash
webpack -p --progress --colors
```

* Congratulations! The frontend of BSC Comorbidities browser is available at the `../REST/static` subdirectory.