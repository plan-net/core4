
### Usage

Usually used inside a pnbi-page with headline as primary Element or title as secondary Table Element

```jsx
  <pnbi-datatable headline="Pnbi Datatable" button-label="New project">
    <!-- Optional Slot-->
    <div slot="primary-controls">
    </div>
    <!-- Optional Slot-->
    <div slot="secondary-controls">
    </div>
    <!-- Default Slot-->
    <v-data-table :headers="pnbiDataTable.headers" :items="pnbiDataTable.items"
    search="" :rows-per-page-items="[10,25,50, {'text':'All','value':-1}]"
    rows-per-page-text="Element per page">
    <template slot="items" slot-scope="props">
      <td>{{props.item.name}}</td>
      <td>{{props.item.age}}</td>
    </template>
    </v-data-table>
  </pnbi-datatable>
```
