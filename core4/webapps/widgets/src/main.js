import Vue from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'

import PnbiBase from 'core4ui/core4'
import 'core4ui/core4/themes/core4/theme-c4.scss'
import THEME from 'core4ui/core4/themes/core4/theme-vuetify'
import { i18n } from 'core4ui/core4/translations'
import VueDragDrop from 'vue-drag-drop'

export const config = {
  THEME,
  TITLE: 'CORE4OS',
  // IGNORED_ERRORS: [],
  APP_IDENTIFIER: 'core'
}
Vue.use(PnbiBase, {
  router,
  config,
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
