import Vue from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'

import Core4ui from 'core4ui/core4'
import 'core4ui/core4/themes/core4/theme-c4.scss'
import VueDragDrop from 'vue-drag-drop'
import THEME from 'core4ui/core4/themes/core4/theme-vuetify'

export const config = {
  THEME,
  TITLE: 'CORE4OS',
  APP_IDENTIFIER: 'core'
}
Vue.use(VueDragDrop)
Vue.use(Core4ui, {
  App,
  router,
  store,
  config
})

/* Vue.config.productionTip = false

new Vue({
  i18n,
  router,
  store,
  render: h => h(App)
}).$mount('#app') */
