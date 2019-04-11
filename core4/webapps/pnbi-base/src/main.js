import Vue from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'

import PnbiBase from 'pnbi-base/core4'
import 'pnbi-base/core4/themes/pnbi/theme-pnbi.scss'
import THEME from 'pnbi-base/core4/themes/pnbi/theme-vuetify'
import { i18n } from 'pnbi-base/core4/translations'

Vue.use(PnbiBase, {
  router,
  config: {
    DARK: true,
    THEME,
    TITLE: 'Welcome to CORE4OS',
    APP_IDENTIFIER: 'welcome-to-core4os'
  },
  store
})

Vue.config.productionTip = false

new Vue({
  i18n,
  router,
  store,
  render: h => h(App)
}).$mount('#app')
