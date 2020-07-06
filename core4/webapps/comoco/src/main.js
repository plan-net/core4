/***
 * TODO: remove moment dependency as it is only used for date formatting
 * TODO: job chart is only visually hidden in low resolutions:  hidden-sm-and-down. It should not be rendered v-if
 * Socket shoul be bound to chart not to app, if chart hidden, sockets still connected
 */
import Vue from 'vue'
import App from './App.vue'
import router from './routes/router'
import store from './store/index'
import VueNativeSock from 'vue-native-websocket'
import moment from 'moment'

/* import PnbiBase from 'core4ui/core4' */
// import 'core4ui/core4/themes/pnbi/theme-pnbi.scss'
/* import THEME from 'core4ui/core4/themes/core4/theme-vuetify' */
// import { i18n } from './translations/index'

import service from './services/comoco.history.service'

/* import '@/style/theme-dark.scss'
import '@/style/theme-light.scss' */

import Core4ui from 'core4ui/core4'
import 'core4ui/core4/themes/core4/theme-c4.scss'
import THEME from 'core4ui/core4/themes/core4/theme-vuetify'
// VeeValidate 3 // todo external file
import { extend, setInteractionMode } from 'vee-validate'
import { required } from 'vee-validate/dist/rules'

export const config = {
  TITLE: 'COMOCO',
  THEME
}
moment.locale('de')
extend('required', {
  ...required,
  message: '{_field_} can not be empty'
})
setInteractionMode('eager')
// VeeValidate 3
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
/* Vue.use(PnbiBase, {
  router,
  config: {
    // DARK: false,
    THEME,
    TITLE: 'COMOCO',
    IGNORED_ERRORS: [],
    APP_IDENTIFIER: 'comoco'
  },
  store
}) */

// =============================================================================================== //
// Extend app with services                                                                        //
// =============================================================================================== //
Vue.use(service)

Vue.use(Core4ui, {
  App,
  router,
  store,
  config
})
