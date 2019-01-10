import Vuex from 'vuex'
import Vue from 'vue'

import voting from './voting'

import createLogger from 'vuex/dist/logger'
Vue.use(Vuex)

export default new Vuex.Store({
  plugins: [createLogger()],
  strict: false,
  modules: {
    voting
  }
})
