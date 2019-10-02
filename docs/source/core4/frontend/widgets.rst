.. _core_config:

#######
Widgets
#######

Widgets are small applications with a very low complexity. They consist of an API and a frontend. In this section, however, we will only deal with the frontend. Information about creating a suitable API can be found here :ref:`api`

Basically you can use any technology to create a widget. But we recommend Vue.js/Vuetify or Jquery/Material design bootstrap.

No matter what technology you use the file structure should be like this.

::

    ├──demo/
    │  ├──demo/
    │  │  ├──api/
    │  │  │  ├──v1/
    │  │  │  │  ├──ressources/        # contains all .py files for a widget
    │  │  │  │  │  ├──templates/      # contains all .html files for a widget
    │  │  │  │  │  │  └──sample.html
    │  │  │  │  │  ├──sample.py
    │  │  │  │  │  ├──__init__.py
    │  │  │  │  ├──server.py          # all endpoints are entered here
    │  │  │  │  ├──__init__.py
    │  │  │  ├──__init__.py
    │  │  ├──__init__.py



Vue.js/Vuetify:
---------------

To get started with Vue.js please visit https://vuejs.org/v2/guide/.

To create a widget using Vue.js the following steps must be followed.
First you create the following HTML file:


.. code-block:: html

    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Sample</title>
        <style>
        </style>
    </head>
    <body>
        <div>
        </div>
    <script>
    </script>
    </body>
    </html>

For widgets created with Vue.js, we provide the files "vue-assets_2.0.js" and "vuetify_2.0.css" on our CDN "https://bi.plan-net.com/cdn" to provide a standardized representation of all widgets. These files are essential for creating a Vue.js widget

vuetify_2.0.css:
    * In order to achieve the same Vuetify status as possible, this file contains a copy of the Vuetify.css file (v2.0.17).
Vue-assets_2.0.js:
    * The Js portion belonging to the version of the Vuetify.css file (v2.0.17)
    * Axios 0.18
    * Vue.js (v2.6.10)
    * Custom JavaScript Snippets for different purposes
    * PNBI_THEME

The default font is Roboto and as icons we use "Material icons", so these have to be included in the head as well.

The HTML file will look like this.


.. code-block:: html

    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Download</title>
        <link href="https://fonts.googleapis.com/css?family=Roboto:100,300,400,500,700,900" rel="stylesheet">
        <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
        <link href="https://bi.plan-net.com/cdn/assets/css/vuetify_2.0.css" rel="stylesheet">
        <style>
        </style>
    </head>
    <body>
        <div>
        </div>
    <script src="https://bi.plan-net.com/cdn/assets/js/vue-assets_2.0.js"></script>
    <script>
    </script>
    </body>
    </html>

The next step is to initialize a Vue instance. You can read more about Vuetify and its HTML Setup here https://vuetifyjs.com/en/getting-started/quick-start. Since Core4OS uses Jinja2 you have to adjust the Vue delimeter now (see :ref:`Jinja2 <jinja>`).

.. code-block:: html

    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Download</title>
        <link href="https://fonts.googleapis.com/css?family=Roboto:100,300,400,500,700,900" rel="stylesheet">
        <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
        <link href="https://bi.plan-net.com/cdn/assets/css/vuetify_2.0.css" rel="stylesheet">
        <style>
        </style>
    </head>
    <body>
        <div id="app">
        </div>
    <script src="https://bi.plan-net.com/cdn/assets/js/vue-assets_2.0.js"></script>
    <script>
      new Vue({
        delimiters: ['[[', ']]'],
        el: '#app',
        data: {
        },
        created() {
        },
        methods: {
        }
      })
    </script>
    </body>
    </html>

The last step is to create a vuetify instance and set the theme. From this point on you can start developing the widget with Vuetify (https://vuetifyjs.com/en/).‪

.. code-block:: html

    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Download</title>
        <link href="https://fonts.googleapis.com/css?family=Roboto:100,300,400,500,700,900" rel="stylesheet">
        <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
        <link href="https://bi.plan-net.com/cdn/assets/css/vuetify_2.0.css" rel="stylesheet">
        <style>
        </style>
    </head>
    <body>
        <div id="app">
            <v-app >
              <v-container>
                <v-btn color="primary"></v-btn>
              </v-container>
            </v-app>
        </div>
    <script src="https://bi.plan-net.com/cdn/assets/js/vue-assets_2.0.js"></script>
    <script>
      new Vue({
        delimiters: ['[[', ']]'],
        el: '#app',
        vuetify: new Vuetify({
          icons: {
              iconfont: 'md',
          },
          theme: window.VUETIFY_THEME
          },
        }),
        data: {
        },
        created() {
        },
        methods: {
        }
      })
    </script>
    </body>
    </html>

Vuetify offers the possibility to use a different icon library than the material design we use, only the integration of the css file in the head and the "iconfont" parameter have to be changed. More detailed information can be found here https://vuetifyjs.com/en/customization/icons


Jquery/Bootstrap Materiel Design
--------------------------------

If the variant with Vue.js/Vuetify is too high an entry hurdle, you can also develop material design with Jquery/Bootstrap. For a first insight please visit https://fezvrasta.github.io/bootstrap-material-design/docs/4.0/getting-started/introduction/

To get a standardized version of the Js-, JQuerycodes as well as Popper and CSS files, core4os has the files "widget.js" and "widget.css".

widget.js includes:
    * JQuery v3.4.0
    * popper
    * Bootstrap material design
    * Theme color Snippet
widget.css:
    * A customized version of the Bootstrap-material-design

Once these two files have been included, https://fezvrasta.github.io/bootstrap-material-design/docs/4.0/getting-started/introduction/ can be used to start developing the widget.


.. code-block:: html

    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>DemoName</title>
        <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
        <link rel="stylesheet" type="text/css" href="{{ default_static('bootstrap-material-design.custom.css') }}">
        <link rel="stylesheet" type="text/css" href="{{ default_static('widget.css') }}">
        <style>
        </style>
    </head>

    <body>
        <div class="container-fluid">

        </div>
    </body>
    <script src="{{ default_static('jq.pop.bsmd.min.js') }}"></script>
    <script>$(document).ready(function() { $('body').bootstrapMaterialDesign(); });</script>

    </body>

    </html>




Dark/Light Theme implementation
-------------------------------

The core4OS widget manager offers the function of a "dark mode". The widget manager adds an URL Parameter to the Widget URL:
http://widgeturl.com?dark=true or http://widgeturl.com?dark=false

The developer must ensure that the widget behaves correctly when the widget is opened.
By including the standard js file
The widget manager sets the class 'theme--dark' or 'theme--light' depending on the 'dark' parameter, which can be found in the widget URL. The second is the default. The developer has the task to adapt background colors and text colors as well as all other contents displayed within the widget to the respective mode. The following code examples describe the procedure.

.. code-block:: css

    .theme--dark header a.display-2 {
        color: white;
    }

By using Vue and Vuetify to create a widget, the developer is relieved of a lot of work when implementing the dark mode, as Vuetify automatically adapts most components.