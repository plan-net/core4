########################
Single Page Applications
########################

Core4os Spas are based on the Material Design System and a variety of modern frontend technologies.

Technologies
============

Core4os Single Page Applications are based on the following technologies:

* VueJS 2.6.x
* Vuetify 1.5.x or 2.0.x
* Core4ui 0.8.x or 1.0.x
* Webpack

In addition the following JavaScript Librairies are used by default:

* vuex
* vue-router
* vue-i18n
* wait
* axios


Prerequisites
#############

An installation of Nodejs including npm is necessary. Yarn is recommended as package manager.

* `Nodejs <https://nodejs.org/en/download/>`_ >= 10
* yarn

 ::

    # install yarn after a succesfull nodejs installation using npm
    npm install -g yarn

 ::

Getting Started
###############

If you're setting up a new project, first create it using the Core4fe Starter Project.
There's everything set up to start developing.

 ::

    # clone core4fe
    git clone https://github.com/plan-net/core4fe.git

    # enter core4fe
    cd core4fe

    # install dependencies
    yarn install

    # start a development server
    yarn serve

 ::

Now you can open your browser to ``http://localhost:808{0-9}``   and start developing.


Developer Setup Frontend
########################

The recommended editor is `visual studio code  <https://code.visualstudio.com/>`_.
The following visual studio code plugins should be installed:

* Eslint (required)
* Vetur (required)
* StandardJS
* vue
* Vue VSCode Snippets
* npm Intellisense
* Path intellisense

Most of this plugins are alsw available for atom, WebStorm and sublime text.

`Additional Information  <https://www.sitepoint.com/vue-development-environment/>`_

Anatomy of a CORE4os Frontend
#############################
 ::

    ├── public/                     # This folder contains public files like index.html and favicon.ico. Any static assets placed here will simply be copied and not go through webpack.
    │   ├── index.html              # index.html template. In CORE4os Application the API Endpoints can be configured here.
    │   └── favicon.ico
    ├── src/                        # >>MOST WORK WILL BE DONE HERE<<. This folder contains the source files for your project.
    │   ├── main.js                 # app entry file
    │   ├── App.vue                 # main app component
    │   ├── components/             # ui components
    │   │   └── ...
    │   └── assets/                 # module assets (processed by webpack)
    │       └── ...
    ├── static/                     # pure static assets (directly copied)
    ├── test/
    │   └── unit/                   # unit tests
    │   │   ├── specs/              # test spec files
    │   │   ├── eslintrc            # config file for eslint with extra settings only for unit tests
    │   │   ├── index.js            # test build entry file
    │   │   ├── jest.conf.js        # Config file when using Jest for unit tests
    │   │   └── karma.conf.js       # test runner config file when using Karma for unit tests
    │   │   ├── setup.js            # file that runs before Jest runs your unit tests
    │   └── e2e/                    # e2e tests
    │   │   └── specs/              # test spec files
    ├── .babel.config.js            # babel config
    ├── .editorconfig               # indentation, spaces/tabs and similar settings for your editor
    ├── .eslintrc.js                # eslint config
    ├── .eslintignore               # eslint ignore rules
    ├── .postcssconfig.js           # postcss config
    ├── package.json                # build scripts and dependencies
    ├── README.md                   # Default README file
    └── vue.config.js               # Configuration of devserver port, Vue version for development, public path on the server etc.

 ::

Configuration  of a CORE4os Frontend
####################################

Api Basepath
------------

There are two different paths which are used in core4os. Please open ``project/public/index.html`` to change these paths.

``window.APIBASE_CORE`` is the path to all CORE4os ressources. This path usually does not need to be changed. These ressources are ``/login``, ``/logout``, ``/profile``, ``/settings``, etc.

``window.APIBASE_APP`` is app specific and usually corresponds to the root variable in the server. See also (see :ref:`api`)