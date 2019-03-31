### Usage

Starter Element for Dialogs with convenience functions
<br><br>

##### Example: Default dialog with two action buttons

```jsx
<div> 
  <v-btn color="accent" small @click="pnbiDialog.open1 = !pnbiDialog.open1">Toggle pnbi-dialog open</v-btn>

  <pnbi-dialog title="Default Dialog" :open="pnbiDialog.open1">
    <!-- Default Slot-->
    <div>What can i do you for?</div>
    <div slot="dialog-actions">
      <v-btn dark color="primary" flat @click="pnbiDialog.open1 = false">
        Cancel
      </v-btn>
      <v-btn dark color="primary" flat>
        Save
      </v-btn>
    </div>
  </pnbi-dialog>
</div> 
```

##### Example: Complete dialog 

```jsx
<div> 
  <v-btn color="accent" small @click="pnbiDialog.open2 = !pnbiDialog.open2">Toggle pnbi-dialog open</v-btn>

  <pnbi-dialog width="100vw" scrollable title="Complete Dialog" :open="pnbiDialog.open2">
    <!-- Default Slot-->
    <div style="min-height: 120vh">Scrollable</div>
    <div slot="dialog-actions">
      <v-btn dark color="primary" flat @click="pnbiDialog.open2 = false">
        Cancel
      </v-btn>
      <v-btn dark color="primary" flat>
        Save
      </v-btn>
    </div>
  </pnbi-dialog>
</div> 
```
