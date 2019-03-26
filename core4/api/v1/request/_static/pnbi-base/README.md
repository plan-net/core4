# pnbi-base

> Authentication, Helpers and Components for PNBI webapps based on VueJS

## Installation

```
yarn add pnbi-base
```

## Development Workflow

1. cd into root directory
2. use the command `yarn link`
3. cd into pnbi-base/starter
4. Run `yarn` for instaling dependencies
5. use the command `yarn link "pnbi-base"`
6. Serve with `yarn run dev` in starter
7. Edit pnbi-base/src
8. Live reload works
9. commit changes after editing
   > Explanation: npm link creates a symlink to root of pnbi-base, so it is not neccessary to edit node_modules/pnbi-base
   > See docs: https://yarnpkg.com/en/docs/cli/link

#### package.json

```bash
"pnbi-base": "https://github.com/marekmru/pnbi-base.git#candidate"
// oder
"pnbi-base": "https://github.com/marekmru/pnbi-base.git"
```

---

### Configuration in src/pnbi.base.js in Host App

```bash
const port = '5000'
const isApiBaseDefined = window.BIAPIBASE != null && !window.BIAPIBASE.includes('echo var')
const basePath = isApiBaseDefined ? window.BIAPIBASE : `http://localhost:${port}`

const BI_BASE_CONFIG = {
  API: basePath,
  MAIN_ROUTE: 'overview',
  TITLE: 'APP_TITLE',
  IGNORED_ERRORS: [500]
}
export default BI_BASE_CONFIG
```

#### src/App.vue in Host App

```bash
<template>
  <pnbi-webapp>
    <side-navigation slot="navigation-slot"></side-navigation>
    <div slot="router">
      <transition name="fade" mode="out-in" :duration="{ enter: 200, leave: 300 }">
        <router-view />
      </transition>
    </div>
  </pnbi-webapp>
</template>
<script>
import SideNavigation from '@/components/SideNavigation'
export default {
  created () {
  },
  components: {
    SideNavigation
  }
}
</script>
<style lang="css" scoped>
</style>
```

#### src/main.js in Host App

```bash
import Vue from 'vue'
import App from './App'
import config from './pnbi.base.config'
import router from './routes'
import store from './store'
import '@/config/filters.js'
// import '@/config/highcharts.js'
import '@/config/packages.js'
import PnbiBase from 'pnbi-base/src'

Vue.use(PnbiBase, {
  router,
  config
})
Vue.config.productionTip = false
/* eslint-disable no-new */
new Vue({
  el: '#app',
  router,
  store,
  components: {
    App
  },
  template: '<App/>'
})
```

##$Helpers / Convenience

### Loader

> Show / Hide loader

```bash
this.$loader(true) // this.$loader(false)
```

> or

```bash
this.$bus.$emit('LOADING', true)
```

> or

```bash
import EventBus from 'pnbi-base/src/event-bus'
EventBus.$emit('LOADING', payload)
```

### EventBus

> Events

```bash
export const LOADING = 'LOADING'
export const PROFILE_UPDATED = 'PROFILE_UPDATED'
export const CONFIG_UPDATED = 'CONFIG_UPDATED'
export const ERROR = 'ERROR'
export const FORBIDDEN = 'FORBIDDEN'
export const TRACK = 'TRACK'
```

> Use EventBus in components

```bash
this.$bus.$emit('LOADING', true)
```

##Available PNBI Components

### pnbi-webapp

> Root for all PNBI webapps
> _See src/App.vue_

##### navigation-slot

Contains your custom navigation for the webapp
TODO: image

##### router

- routerview and wrapping transitiongroup
- dialogs and components which should be globally available
  > Example: Dialog

---

## pnbi-page

> Used as Top Level Element for Pages / Routes

#### Slots

##### page-header-content (optional)

Main KPIS for the page, Name of the active Entity

##### default slot (no name)

Any HTML

#### Attributes

- header-type: 1|2|3|4
- small | medium | large: height of the header

#### Markup

```javascript
<pnbi-page header-type="2" medium>
  <div slot="page-header-content">
    <header-element />
  </div>
  <div>I am the content slot</div>
</pnbi-page>
```

## ![PNBI Page](https://github.com/marekmru/pnbi-base/blob/candidate/src/assets/pnbi-page.jpg "PNBI Page")

## pnbi-datatable

> Usually used inside a pnbi-page with headline as VIP or title as secondary Table Element

#### Slots

##### primary-controls (optional)

Searchfield + Button

##### secondary-controls (optional)

Slot for Line with additional Controls for the datatable

##### default slot (no name)

Vuetify Datatable

#### Attributes

- headline: Larger Headline
- title: Smaller Headline for second Table on a page
- button-label: "Neues Element"
- flat | default: false; true|false
- customise-label | default: false. Set the label for customise feature

#### Events / Emits

- new: Click on New Button
- search: String with content of the searchfield

#### Markup

```javascript
    <pnbi-datatable headline="Pagename" @search="search = $event" button-label="Neues Projekt" @new="dialogOpen = !dialogOpen">
      <!-- Optional Slot-->
      <div slot="primary-controls">
      </div>
      <!-- Optional Slot-->
      <div slot="secondary-controls">
      </div>
      <!-- Default Slot-->
      <v-data-table :headers="headers" :items="computedProjects" :search="search" :rows-per-page-items="[10,25,50, {'text':'Alle','value':-1}]" rows-per-page-text="Elemente pro Seite" :loading="!computedProjects">
            <!-- See Vuetify-->
      </v-data-table>
    </pnbi-datatable>
```

---

## pnbi-datatable-plus

> Used for displaing rich datatables.Features as column-sorting, serverside pagination and fixed-header are available

This is a wrapper for v-data-table and acceps all attributes and slots from
original v-data-table.

##### Attributes

`tableIdentifier` - id for table. It should be uniq in all applications. Example `tableIdentifier="{app}-{pagename}"`. We use this ID for storage selected columns in browser localstorage.

### Features

#### Column filterng

Enabled by default. This feature makes posible to filter the columns. You can hide some columns. The selected set of columns are saved to localstorage in browser.

#### Server side pagination

Disabled by default. Enable it by defining folowing props:

Define `total-items` prop. Total-items prop will disable the built-in frontend sorting and pagination. Define `loading` prop. Use Loading prop to display a progress bar while fetching data.

Define listener for events: `@padinationEvent="onPaginationEvent"` this event is fired if user change something in the pagination. So you take new pagination object and make a request to the backend:

```javascript
onPaginationEvent (data, event) {
  // update pagination
  this.request.pagination = data
  this.getDataFromApi(this.request)
    .then(data => {
      this.items = data.items
      this.totalItems = data.totalItems
    })
}
```

Your data object:

```javascript
data: () => {
  return {
    items: [],
    totalItems: 0,
    loading: true,
    request: {
      pagination: {},
      search: null
    },
    headers: [
      { text: "Name 2", value: "name" },
      { text: "Age", value: "age" },
      { text: "Value", value: "value" }
    ]
  };
};
```

Wrap API endpoint request params in request object and send to Backend:

1. `page` - page number (int)
2. `rowsPerPage` - rows count per page (int)
3. `sortBy` - column to sort by (string)
4. `descending` - flag for sorting (boolean)

Request Example:

```json
request: {
  pagination: {
    "descending":false,
    "page":1,
    "rowsPerPage":5,
    "sortBy":"name"
    },
  search: null
}
```

Response should include:

1. `totalItems` - length of found items list
2. `items` - plain list of items

## Markup

Use default slot inside of pnbi-datatable. Let `secondary-controls` slot blank. Datatable plus has own toolbar with controls.

```html
<pnbi-datatable headline="Headline">
  <!-- don't use secondary slot -->
  <!-- default slot -->
    <pnbi-datatable-plus
      :items="items" :headers="headers" :loading="loading" tableIdentifier="123" :total-items="totalItems" @padinationEvent="onPaginationEvent">
      <tr slot="row" slot-scope="props">
        <td>{{props.props.item.name}}</td>
        <td>{{props.props.item.age}}</td>
        <td>{{props.props.item.value}}</td>
      </tr>
    </pnbi-datatable-plus>

</pnbi-datatable>
```

#### Fixed header & Footer

Disabled by default. Enable it by defining folowing props:

Define `fixed-header` prop. It makes header be always visible. If user scroll to the end of a large table header positioned sticky on top of application. Define `fixed-footer` prop. It makes header be always visible. If user scroll to the end of a large table header positioned sticky on bottom of application.

Place footer template inside of `footer` slot

## pnbi-card

> Usually used inside a pnbi-page with headline as VIP or title as secondary Table Element
> Default Conainer Element for any kind of content

#### Slots

##### primary-controls (optional)

Searchfield + Button

##### default slot (no name)

card-content placed inside _v-card-text_

##### card-actions

Optional Content, for example Buttons

#### Attributes

- headline: Larger Headline
- title: Smaller Headline for second Table on a page

#### Markup

```javascript
    <pnbi-card headline="Pagename"  >
      <!-- Optional Slot-->
      <div slot="primary-controls">
      </div>
      <!-- Default Slot-->
      <div>Any Content can be placed here with any tag</div>
      <!-- Optional Slot-->
      <div slot="card-actions">
      </div>
    </pnbi-card>
```

---

## pnbi-dialog

> Starter Element for Dialogs with convenience functions

#### Slots

##### primary-controls (optional)

Searchfield + Button

##### default slot (no name)

card-content placed inside _v-card-text_

##### dialog-actions

Optional Content, for example Buttons

#### Attributes

- title: Headline of the Dialog
- scrollable: default: false - true|false
- width: default: 640px: '900'|'90%'|'90vw'
- open: default: false - true|false

#### Events / Emits

- @close

#### Markup

```javascript
  <pnbi-dialog :open="booleanInParent" :scrollable="true" @close="booleanInParent = false" width="1440px" title="Koeffizienten">
      <div slot="dialog-content">
        What can i do you for?
      </div>
      <div slot="dialog-actions">
        <v-btn dark color="primary" flat @click.native="booleanInParent = false">
          Abbrechen
        </v-btn>
        <v-btn dark color="primary" flat @click.native="booleanInParent = false">
          Ok
        </v-btn>
    </div>
  </pnbi-dialog>
```

---

## pnbi-empty

> No Content available Element

#### Attributes

- data: Object

```javascript
{
  label: "Keine Widgets geladen. Bitte laden."; // oder
  html: "<span><strong>Keine Widgets</strong>vorhanden</span>";
}
```

#### Markup

```javascript
  <pnbi-empty :data="{label: 'Keine Zielgruppen vorhanden.'}"></pnbi-empty>
```
