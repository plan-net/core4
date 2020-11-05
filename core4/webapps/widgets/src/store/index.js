import Vue from 'vue'
import Vuex from 'vuex'
import widgets from '@/store/widgets'
/* import createLogger from 'vuex/dist/logger'
const debug = process.env.NODE_ENV !== 'production'
const plugins = debug ? [createLogger({})] : [] */
Vue.use(Vuex)
export default new Vuex.Store({
  // plugins,
  modules: {
    widgets
  }
})
