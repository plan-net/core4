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

import service from './services/comoco.history.service'

import Core4ui from 'core4ui/core4'

import { extend, setInteractionMode } from 'vee-validate'
import { required } from 'vee-validate/dist/rules'

export const config = {
  TITLE: 'COMOCO'
}
moment.locale('de')
extend('required', {
  ...required,
  message: '{_field_} can not be empty'
})
setInteractionMode('eager')
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
// Extend app with services                                                                        //
// =============================================================================================== //
Vue.use(service)

Vue.use(Core4ui, {
  App,
  router,
  store,
  config: {
    TITLE: 'COMOCO'
  }
})
