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
