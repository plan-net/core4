import Vue from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'
import VueNativeSock from 'vue-native-websocket'

import PnbiBase from 'core4ui/core4'
// import 'core4ui/core4/themes/pnbi/theme-pnbi.scss'
import THEME from 'core4ui/core4/themes/core4/theme-vuetify'
import { i18n } from 'core4ui/core4/translations'

import service from './service'

import '@/style/theme-dark.scss'
import '@/style/theme-light.scss'

// =============================================================================================== //
// Extend app with native WebSocket                                                                //
// =============================================================================================== //
Vue.use(VueNativeSock, ' ', {
  store: store,
  format: 'json',
  connectManually: true,
  reconnection: true, // reconnect automatically
  reconnectionAttempts: 5, // number of reconnection attempts before giving up (Infinity),
  reconnectionDelay: 3000 // how long to initially wait before attempting a new (1000)
})

// =============================================================================================== //
// Extend app with PnbiBase feature                                                                //
// =============================================================================================== //
Vue.use(PnbiBase, {
  router,
  config: {
    // DARK: false,
    THEME,
    TITLE: 'COMOCO',
    IGNORED_ERRORS: [],
    APP_IDENTIFIER: 'comoco'
  },
  store
})

// =============================================================================================== //
// Extend app with services                                                                        //
// =============================================================================================== //
Vue.use(service)

Vue.config.productionTip = false

new Vue({
  i18n,
  router,
  store,
  render: h => h(App)
}).$mount('#app')
