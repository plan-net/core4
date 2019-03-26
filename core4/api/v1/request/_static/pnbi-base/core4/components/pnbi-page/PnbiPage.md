### Usage

Used as Top Level Element for Pages / Routes
<br><br>

##### Example: Header-type: 2 and size: large

```jsx
<div style="min-height: 400px;" class="pa-3">

  <pnbi-page header-type="2" large>
    <div slot="page-header-content">
      <h3 class="subtitle pt-5 white--text">Pageheader Contains information about content displayed on the page. Important kpis or filter elements.</h3>
    </div>

    <pnbi-card title="Page with pnbi-card">
      <div slot="primary-controls">
        <v-btn color="accent" small>Download CSV</v-btn>
      </div>
      <!-- Default Slot-->
      <div>Lorem ipsum dolor sit amet, consectetur adipisici elit, sed eiusmod tempor incidunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquid ex ea commodi consequat. Quis aute iure reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint obcaecat cupiditat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.</div>

      <div slot="card-actions">
        <v-btn flat color="primary">More</v-btn>
      </div>
    </pnbi-card>

  </pnbi-page>

</div>
```

<br><br>

##### Example: Header-type: 1 and size: medium

```jsx
<div style="min-height: 400px;" class="pa-3">

  <pnbi-page header-type="1" medium>

    <pnbi-card title="Page with pnbi-card">
      <div slot="primary-controls">
        <v-btn color="accent" small>Download CSV</v-btn>
      </div>
      <!-- Default Slot-->
      <div>Lorem ipsum dolor sit amet, consectetur adipisici elit, sed eiusmod tempor incidunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquid ex ea commodi consequat. Quis aute iure reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint obcaecat cupiditat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.</div>

      <div slot="card-actions">
        <v-btn flat color="primary">More</v-btn>
      </div>
    </pnbi-card>

  </pnbi-page>

</div>
```
