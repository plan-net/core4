import Vue from 'vue'
import Vuex from 'vuex'
import createLogger from 'vuex/dist/logger'

import state from './comoco.state'
import actions from './comoco.actions'
import getters from './comoco.getters'
import mutations from './comoco.mutations'

const debug = process.env.NODE_ENV !== 'production'
const plugins = debug ? [createLogger({})] : []

Vue.use(Vuex)

export default new Vuex.Store({
  plugins,
  state,
  actions,
  mutations,
  getters
})
