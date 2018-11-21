import Vue from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'
import VeeValidate from 'vee-validate'
import VueSSE from 'vue-sse'
import PnbiBase from 'pnbi-base/src'
/* import VueParticles from 'vue-particles'

Vue.use(VueParticles) */

Vue.use(PnbiBase, {
  router,
  config: {
    FALLBACK: '5001/voting/v1',
    TITLE: 'VOTING',
    IGNORED_ERRORS: []
  },
  store
})
VeeValidate.Validator.extend('json', {
  getMessage: field => '' + field + ' muss valides JSON enthalten.',
  validate: value => {
    try {
      JSON.parse(value)
      return true
    } catch (error) {
      return false
    }
  }
})

Vue.use(VueSSE)
Vue.config.productionTip = false

new Vue({
  router,
  store,
  render: h => h(App)
}).$mount('#app')
