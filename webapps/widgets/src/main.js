import Vue from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'

import PnbiBase from 'pnbi-base/core4'
// import 'pnbi-base/core4/themes/pnbi/theme-pnbi.scss'
import THEME from 'pnbi-base/core4/themes/pnbi/theme-vuetify'
import { i18n } from 'pnbi-base/core4/translations'
import VueDragDrop from 'vue-drag-drop'

Vue.use(PnbiBase, {
  router,
  config: {
    xxxDARK: true,
    xxxEMAIL: 'bi-ops@plan-net.com',
    THEME,
    TITLE: 'CORE IV',
    IGNORED_ERRORS: [],
    APP_IDENTIFIER: 'core'
  },
  store
})

Vue.use(VueDragDrop)
Vue.config.productionTip = false

new Vue({
  i18n,
  router,
  store,
  render: h => h(App)
}).$mount('#app')
