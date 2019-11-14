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

Most of this plugins are available for atom, WebStorm and sublime text.

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



Configuration  of a CORE4os Frontend
####################################

Api Basepath
------------

There are 2 different paths used in core4os: ``VUE_APP_APIBASE_CORE`` and ``VUE_APP_APIBASE_APP``.
These two paths are defined in the ".env", ".env.development" and ".env.production" files.
These files can be found in the root directory of the frontend application.
If these files do not exist, they must be inserted there.
The difference between the individual files are the modes in which the application is located.
During the development and execution of 'yarn serve' the application is in development mode.
In this mode the '.env.development' file is used.
However, if the application is running on the server, it is in production mode, so the ".env.production" is the dominant file.
If there is no suitable file in one of the two modes, the ".env" file is used.
The paths described above are now defined within the appropriate file.

.env
VUE_APP_APIBASE_CORE=/core4/api/v1VUE_APP_APIBASE_APP=/<< app-name >>/api/v1

.env.development
VUE_APP_APIBASE_CORE=http://localhost:5001/core4/api/v1VUE_APP_APIBASE_APP=http://localhost:5001/<< app-name >>/api/v1

.env.production
VUE_APP_APIBASE_CORE=/core4/api/v1VUE_APP_APIBASE_APP=/<< app-name >> /api/v1


There are two different paths which are used in core4os. Please open ``project/public/index.html`` to change these paths.

``window.APIBASE_CORE`` is the path to all CORE4os ressources. This path usually does not need to be changed. These ressources are ``/login``, ``/logout``, ``/profile``, ``/settings``, etc.

``window.APIBASE_APP`` is app specific and usually corresponds to the root variable in the server. See also (see :ref:`api`)

package.json
------------
The following settings can be made in the package.json:

* ``"name": "app-name"`` should be updated according to the application that is beeing developed
* the field ``"core4ui": "^1.0.22"`` can be updated to the latest version of core4ui. Currently it is version 1.0.22.

The package.json contains control commands for the core4os build system. These can, but don't have to be changed.

.. code-block:: js

    "core4": {
    "build_command": [
      "rm yarn.lock",
      "yarn install",
      "yarn build --dest dist --modern"
    ],
    "dist": "./dist"
    },

core4ui lib
------------
The core4ui library can be configured in the file ``src/main.js``.

.. code-block:: js

    import Vue from 'vue'
    import App from './App.vue'
    import router from './router'
    import store from './store'
    import Core4ui from 'core4ui/core4'
    import 'core4ui/core4/themes/core4/theme-c4.scss'
    import THEME from 'core4ui/core4/themes/core4/theme-vuetify'
    export const config = {
      THEME,
      TITLE: 'CORE4OS',
      APP_IDENTIFIER: 'core'
    }
    Vue.use(Core4ui, {
      App,
      router,
      store,
      config
    })

The configuration object contains the title, which is displayed within the application, the ``store`` and ``router``,
which are merged with the core4ui router and store, a reference to the ``app`` object and some ``scss and theme configuration`` files.
The user can customize the sass and theme files and pass his own variants.

Store
*****

The core4ui store contains application wide information.
These are user profiles, settings made by the user, and settings required for functions of the application.
.. code-block:: js

    const state = {
      hasOwnTheme: false,   // Disable / enable the possibility to choose between the light or the dark theme
      dark: false,          // Current theme - light or dark
      appBarVisible: true,  // Show or hide the application navbar
      loading: false,       // Show or hide the application loading bar
      inWidget: false,      // Adds or removes functionality if a webapp is shown inside the widget manager (close button)

      title: 'Application Name', // the displayed application name, configured in ``core4ui lib``
      menu: [],                  // array of items that are available through the navigation bar menu
      profile: {                 // general user information
        error: null,
        authenticated: false,
        name: null,
        email: 'No email'
      }
    }