### Usage

Component for displaying formatted numbers.<br>Model: 1000000, Display: 1.000.000 € or 1.000 T€.

<br><br>

##### Example:
```jsx
<p class="pa-3">

  <pnbi-numbers 
  
  label="Budget 1" 
  data-vv-as="Budget 1" 
  data-vv-name="Budget 1" 
  v-validate="'required|between:0,100000'" 
  :error-messages="errors.collect('Budget 1')" 
  v-model="pnbiNumbersModel.item1"
  suffix="T€"
  :unit="1000" />

  <pnbi-numbers 
  label="Budget 2" 
  data-vv-as="Budget 2" 
  data-vv-name="Budget 2" 
  v-validate="'required|between:0,1000'" 
  :error-messages="errors.collect('Budget 2')" 
  v-model="pnbiNumbersModel.item2"
  suffix="€"
  :unit="1" />

  <pnbi-numbers 
  label="Budget 3" 
  data-vv-as="Budget 3" 
  data-vv-name="Budget 3" 
  v-validate="'required|between:0,10'" 
  :error-messages="errors.collect('Budget 3')" 
  v-model="pnbiNumbersModel.item3"
  suffix="€"
  :unit="1" />

</p>
```

<br><br>
