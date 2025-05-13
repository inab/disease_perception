# Install instructions of Disease PERCEPTION 1 Comorbidities browser

The source code of this browser is written for Javascript ES6. It depends on the libraries declared in [package.json](package.json) file.

* In order to compile the dependencies you need to have installed latest stable [NodeJs](http://nodejs.org/) release, either using your operating system / distribution package manager, or by hand. If you have installed NodeJs by hand, remember to add its `bin` subdirectory to the `PATH` environment variable.
  
* Clone this repository, change to the directory `FRONTEND` and assure newest version of `npm` is installed:

```bash
git clone https://github.com/inab/disease_perception.git
cd FRONTEND
# These are needed to prefer git+https over git+ssh
git config --global url."https://github".insteadOf ssh://git@github
git config --global url."https://github.com/".insteadOf git@github.com:
npm install --no-save npm node-gyp
```

* Next line installs [Yarn](https://yarnpkg.com/) installation dependency, which is used to fetch [Webpack](https://webpack.github.io/) and other dependencies:

```bash
npm x -- npm install --no-save yarn
```

* Then, call `yarn`, so the other dependencies are fetched:

```bash
npm x -- yarn install --frozen-lockfile
```

* Now, you have to run `webpack` in order to prepare and deploy the BSC Comorbidities browser site, which will be deployed at `../REST/static` subdirectory.

```bash
npm x -- webpack -p --progress --colors
```

* Congratulations! Disease PERCEPTION 1 Comorbidities browser is available at the `../REST/static` subdirectory.
