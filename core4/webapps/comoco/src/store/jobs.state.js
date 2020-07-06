// import { BUSY_ON, BUSY_OFF } from '@/external/types.js'
import api, { getSSE } from '@//api/api2.js'
import { extractError, formatDate } from '@/components/misc/helper.js'
import _ from 'lodash'
import store from '@/store'
import Vue from 'vue'

let sses = []
let ti, tiFetchJobs
function clearSSE (e) {
  // console.log('clearSSE')
  try {
    if (e != null) {
      e.source.removeEventListener('log')
      e.source.removeEventListener('update')
      e.source.removeEventListener('close')
      e.source.removeEventListener('error')
    } else {
      sses.forEach(sse => {
        sse.removeEventListener('log')
        sse.removeEventListener('update')
        sse.removeEventListener('close')
        sse.removeEventListener('error')
        sse.close()
      })
      sses = []
    }
  } catch (err) {
  }
}
function onSseError (e) {
  if (typeof e.error === 'string') {
    const extracted = JSON.parse(e.error)
    const errorRaw = extractError(extracted.error)
    store.commit('jobs/addError', errorRaw)
  }
}
const state = {
  filter: null,
  log: [],
  error: null,
  job: { _id: null },
  jobs: []
}

const actions = {
  /**
   * Error occured in sse, add extracted errormessages,
   * which is meant to be displayed in components validation
   *
   */
  clearJobError (context) {
    context.commit('addError', null)
  },
  clearJob (context, sse) {
    context.commit('clearJob', null)
    context.commit('clearJobs')
    context.commit('clearLog')
    context.commit('addStateFilter', null)
    window.clearTimeout(ti)
    window.clearTimeout(tiFetchJobs)
    if (sses.length > 0) {
      clearSSE()
    }
    return true
  },
  addLog (context, payload) {
    context.commit('addLog', payload)
  },
  setJob (context, job) {
    context.commit('setJob', job)
    context.dispatch('logJob', job._id)
  },
  async fetchJob (context, id) {
    const job = await api.get(`jobs/${id}`)
    context.commit('setJob', job.data)
    return job.data
  },
  logJob (context, jobId = null) {
    context.commit('clearLog')
    // clearSSE()
    const id = jobId || state.job._id
    const token = JSON.parse(localStorage.getItem('user')).token
    const json = {
      identifier: id,
      start: state.job.started_at
    }
    const sse = getSSE({
      endpoint: `log?token=${token}`,
      json
    })
    sses.push(sse)
    sse.addEventListener('log', e => {
      const json = JSON.parse(e.data)
      const { message, epoch, level } = json
      context.dispatch('addLog', {
        message,
        date: formatDate(new Date(epoch * 1000)),
        level
      })
    })
    sse.addEventListener('error', onSseError)
    sse.addEventListener('close', clearSSE)
    sse.stream()
  },
  updateJob (context, delta) {
    context.commit('updateJob', delta)
  },
  /**
   * Used for sse on new enqueud job
   * Use on existion job group
   *
   */
  pollEnqueuedJob (
    context,
    conf = {
      job: null
    }
  ) {
    return new Promise((resolve, reject) => {
      context.commit('addError', null)
      // clearSSE()
      context.commit('clearJob')

      const token = JSON.parse(localStorage.getItem('user')).token
      const endpoint = `jobs/poll/${conf.job._id || conf.job}?token=${token}`
      const sse = getSSE({
        endpoint
      })

      sse.addEventListener('update', function (e) {
        const delta = JSON.parse(e.data)
        // console.log('update', delta)
        context.dispatch('updateJob', delta)
        window.clearTimeout(ti)
        ti = window.setTimeout(function () {
          context.commit('cleanupCompletedJobs')
        }, 2500)
      })
      sse.addEventListener('log', function (e) {
        const json = JSON.parse(e.data)
        const message = {
          message: json.message,
          date: formatDate(new Date()),
          level: null
        }
        context.dispatch('addLog', message)
      })
      sse.addEventListener('error', e => {
        onSseError(e)
      })
      sse.addEventListener('close', clearSSE)
      sse.stream()
      sses.push(sse)
    })
  },
  async enqueueJob (context, payload) {
    context.dispatch('clearJob')
    const name = payload.job
    const args = payload.args
    const dto = Object.assign({}, args, { name })

    let job
    try {
      const ret = await api.post(
        'jobs/enqueue', dto

      )
      job = ret.data
      context.commit('setJob', job) // only name, id, triggers dialog to open, starts logging
      context.dispatch('fetchJob', job._id).then(val => {
        context.commit('setJobs', [val])
      })
      context.dispatch('pollEnqueuedJob', {
        job
      })
      context.dispatch('pollEnqueuedJob', {
        job: job.name
      })
      return true
    } catch (error) {
      const errorRaw = extractError(error.response.data.error)
      store.commit('jobs/addError', errorRaw)
    }
  },
  async fetchJobsByName (context, payload) {
    const json = {
      filter: {
        name: payload.name
      }
    }
    const jobs = await api.post('jobs?per_page=1000&page=0', json)
    // clicked state first, then other states
    const sortedJobs = jobs.data.sort(function compare (a, b) {
      if (a.state === payload.state) {
        return -1
      }
      if (a.state !== payload.state) {
        return 1
      }
      return 0
    })
    context.commit('setJobs', sortedJobs)
    context.dispatch('pollEnqueuedJob', {
      job: payload.name
    })
    if (jobs.data.length > 0) {
      // select by state
      const selected = jobs.data.find(val => val.state === payload.state)
      context.dispatch('setJob', _.cloneDeep(selected || jobs.data[0]))
    }
  },
  async addStateFilter (context, states) {
    context.commit('addStateFilter', states)
  },
  async manageJob (context, action = 'restart') {
    window.clearTimeout(tiFetchJobs)
    const current = _.cloneDeep(context.state.job)
    try {
      await api.put(`jobs/${action}/${context.state.job._id}`)
      // context.commit('removeJob', current._id)
      tiFetchJobs = window.setTimeout(function () {
        context.dispatch('fetchJobsByName', current)
      }, 2500)
      // context.dispatch('fetchJobsByName', current)
    } catch (err) {
      Vue.prototype.raiseError(err)
    } finally {
    }
  }
}

const mutations = {
  addStateFilter (state, payload) {
    state.filter = payload
  },
  addLog (state, payload) {
    state.log = (state.log || []).concat([payload])
  },
  clearLog (state, payload) {
    state.log = []
  },

  addError (state, payload) {
    state.error = payload
  },
  clearJobs (state) {
    state.jobs = []
  },
  clearJob (state) {
    state.job = { _id: null }
  },
  removeJob (state, id) {
    state.jobs = state.jobs.filter(val => val._id !== id)
    if (state.job._id === id) {
      state.job = state.jobs[0] || null
    }
  },
  cleanupCompletedJobs (state) {
    state.jobs = state.jobs.filter(val => {
      if (val.state !== 'complete') {
        return true
      }
      if (state.job._id === val._id) {
        state.job = state.jobs[0] || null
      }
      return false
    })
  },
  updateJob (state, delta) {
    state.jobs = state.jobs.map(val => {
      /*       Object.keys(delta).forEach(key => {
        if (
          typeof val[key] === 'string' &&
          delta[key] !== val[key]
        ) {
          console.log('update', val._id, key, val[key], '>', delta[key])
          console.log('--------------------------------------')
        }
      }) */
      if (val._id === delta._id) {
        val = _.merge(val, delta)
        if (state.job._id === delta._id) {
          state.job = val
        }
      }
      return val
    })
  },
  setJobs (state, payload) {
    state.jobs = payload || []
  },
  setJob (state, payload) {
    state.job = payload
  }
}

const getters = {
  job (state) {
    return state.job
  },

  filter (state) {
    return state.filter
  },
  jobs (state) {
    return state.jobs
  },
  filteredJobs (state) {
    if (state.filter != null && Array.isArray(state.filter)) {
      return state.jobs.filter(val => {
        if (state.filter.includes(val.state)) {
          return true
        }
        return false
      })
    }
    return state.jobs
  },
  log (state) {
    return state.log
  }
}
export default {
  namespaced: true,
  state,
  actions,
  mutations,
  getters
}
