import Vue from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'

import Core4ui from 'core4ui/core4'

Vue.use(Core4ui, {
  App,
  router,
  store,
  config: {
    TITLE: 'Core4os'
  }
})
