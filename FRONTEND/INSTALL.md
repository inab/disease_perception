# Install instructions of Disease PERCEPTION Comorbidities browser

The source code of this browser is written for Javascript ES6. It depends on the libraries declared in [package.json](package.json) file.

* In order to compile the dependencies you need to have installed latest stable [NodeJs](http://nodejs.org/) release, either using your operating system / distribution package manager, or by hand. If you have installed NodeJs by hand, remember to add its `bin` subdirectory to the `PATH` environment variable.

  - Due some intermediate dependencies, you could also need `ruby` and `gem`.
  
* Clone this repository, change to the directory `FRONTEND` and assure newest version of npm is installed:

```bash
git clone https://github.com/inab/comorbidities_frontend.git
cd FRONTEND
npm install --no-save npm
```

* Add `node_modules/.bin` subdirectory to the `PATH` environment variable, so newest `npm`, `yarn` and other installation dependencies can be instantiated:

```
PATH="$(npm bin):${PATH}"
export PATH
```

* Next line installs [Yarn](https://yarnpkg.com/) installation dependency, which is used to fetch [Webpack](https://webpack.github.io/) and other dependencies:

```
npm install --no-save yarn
```

* Then, call `yarn`, so the other dependencies are fetched:

```bash
yarn --frozen-lockfile
```

* Now, you have to run `webpack` in order to prepare and deploy the BSC Comorbidities browser site, which will be deployed at `../REST/static` subdirectory.

```bash
webpack -p --progress --colors
```

* Congratulations! Disease PERCEPTION Comorbidities browser is available at the `../REST/static` subdirectory.
