import Vue from 'vue'
import Vuex from 'vuex'

import history from '@/store/history.state.js'
import jobs from '@/store/jobs.state.js'
import app from '@/store/app.state.js'
/*
import createLogger from 'vuex/dist/logger'
const debug = process.env.NODE_ENV !== 'production'
const plugins = debug ? [createLogger({})] : [] */

Vue.use(Vuex)

export default new Vuex.Store({
  plugins: [],
  strict: true,
  modules: {
    app,
    history,
    jobs
  }
})
