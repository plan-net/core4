### Usage

Root component for all plan.net business intelligence webapps
<i>router not working with vue-styleguidist - so just code.<i/>
#### Code

```js static
  <pnbi-webapp>
    <side-navigation slot="navigation-slot"></side-navigation>
    <router-view slot="router"></router-view>
  </pnbi-webapp>

  <pnbi-webapp full-width>
    <side-navigation></side-navigation>
    <router-view slot="router"></router-view>
  </pnbi-webapp>
```