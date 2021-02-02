import Vue from 'vue'
// import { clone } from 'core4ui/core4/helper'
import _ from 'lodash'
import {
  jobGroups,
  jobTypes,
  jobFlags,
  jobStates,
  eventChannelNames
} from '../settings'
import {
  SOCKET_ONOPEN,
  SOCKET_ONCLOSE,
  SOCKET_ONERROR,
  SOCKET_ONMESSAGE,
  SOCKET_RECONNECT,
  SOCKET_RECONNECT_ERROR,
  NOTIFICATION_CHANGE_STATE
} from './comoco.mutationTypes'

import { deepMerge, createObjectWithDefaultValues } from '../helper'

const defaultEventObj = createObjectWithDefaultValues(jobTypes, 0)
const channelDict = {
  queue: {
    // on_queue:
    summary: queueChannelHandler,

    // on_event:
    ...eventChannelNames.reduce((computedResult, currentItem) => {
      computedResult[currentItem] = eventChannelHandler

      return computedResult
    }, {})
  }
}

const state = {
  queue: {
    // queue object interface:
    //   stat: {
    //     running: 0,
    //     pending: 0,
    //     deferred: 0,
    //     failed: 0,
    //     error: 0,
    //     inactive: 0,
    //     killed: 0,
    //     created: "2019-05-21T20:24:05.180000"
    //   },
    //   running: [],
    //   stopped: [],
    //   waiting: []
  },
  event: {
    // event object interface:
    //   running: 0,
    //   pending: 0,
    //   deferred: 0,
    //   failed: 0,
    //   error: 0,
    //   inactive: 0,
    //   killed: 0,
    //   created: "2019-05-21T20:24:05.180000"
  },
  socket: {
    isConnected: false,
    message: '',
    reconnectError: false
  },
  notifications: {
    socket_reconnect_error: {
      state: false, // false = hide, true = show
      type: 'error',
      dismissible: false, // show "close button" parameter
      // timeout: 7000,
      message: '',
      slot: '',
      inComponents: ['home']
    }
  }
}
const actions = {}

const mutations = {
  [SOCKET_ONOPEN] (state, event) {
    Vue.prototype.$socket = event.currentTarget
    Vue.prototype.$socket.sendObj({
      type: 'interest',
      data: ['queue', 'event', 'job']
    })

    state.socket.isConnected = true
    state.socket.reconnectError = false
  },
  [SOCKET_ONCLOSE] (state) {
    // state.socket.isConnected = false
  },
  [SOCKET_ONERROR] (state, event) {
    console.error(state, event)
  },
  // default handler called for all methods
  [SOCKET_ONMESSAGE] (state, message) {
    state.socket.message = message
    if (message.channel && message.name) {
      channelDict[message.channel][message.name](state, message)
    }
  },
  // mutations for reconnect methods
  [SOCKET_RECONNECT] (state, count) {
    console.info(state, count)
  },
  [SOCKET_RECONNECT_ERROR] (state) {
    // ToDo: add error flow (message, pop-up etc)
    state.socket.isConnected = false
    state.socket.reconnectError = true
  },
  [NOTIFICATION_CHANGE_STATE] (state, payload) {
    deepMerge(state.notifications[payload.name], payload.data)
  }
}

const getters = {
  ...mapGettersJobGroups(jobGroups), // getter for each job type (pending, deferred, ..., killed)
  getJobsByGroupName: (state, getters) => groupName => getters[groupName],
  getStateCounter: state => stateName => {
    if (state.queue.stat === undefined) return 0

    return stateName.reduce((previousValue, currentItem) => {
      previousValue += state.queue.stat[currentItem] || 0

      return previousValue
    }, 0)
  }
}
export default {
  namespaced: false,
  state,
  actions,
  mutations,
  getters
}
// ================================================================= //
// Private methods
// ================================================================= //

/**
 * Getter(s) for job(s) group from store
 *
 * @param {array} arr -  group(s)
 *                       e.g. ['waiting', 'running', 'stopped']
 *
 * @returns {object} - object with key - group name, value - getter function
 *                     e.g. {'running': (state) => f, ...}
 */
function mapGettersJobGroups (arr) {
  return arr.reduce((computedResult, currentItem) => {
    computedResult[currentItem] = state => {
      return _.cloneDeep(state.queue[currentItem] || [])
    }

    return computedResult
  }, {})
}

// ================================================================= //
// Private methods
// ================================================================= //
/**
 * Handler for queue notification
 *
 * @param state {object} - store state
 * @param message {object} - ws notification
 */
function queueChannelHandler (state, message) {
  // summary - ws type notification (all jobs in queue)
  state.queue = groupDataAndJobStat(message.created, message.data, 'state')

  if (!state.socket.reconnectError) {
    // ToDo: check on prod
    // console.log('event = queue.stat')
    state.event = state.queue.stat
  }
}

/**
 * Handler for event notification
 *
 * @param state {object} - store state
 * @param message {object} - ws notification
 */
function eventChannelHandler (state, message) {
  state.event = { ...defaultEventObj, ...message.data.queue }
  state.event.created = message.created
}

/**
 * Assort array of all jobs in groups + get job statistic
 *
 * @param {string} created - timestamp
 * @param {array} arr - array of all jobs
 * @param {string} groupingKey - job object key by which we will do grouping
 *
 * @returns {object} - grouped jobs object
 *                     e. g. {'stat': {'waiting': 5, ...}, 'running': [<job>, ..., <job>], ...}
 */
// ToDo: elegant decouple group data and job statistic
function groupDataAndJobStat (created, arr, groupingKey) {
  const groupsDict = {}
  const initialState = createObjectWithDefaultValues(jobStates)

  arr.forEach(job => {
    if (!job.key) job.key = uniqueKey(job)

    const jobState = job[groupingKey]
    const group = jobStates[jobState] || 'other';

    (groupsDict[group] = groupsDict[group] || []).push(job)

    initialState[jobState] += job.n
    initialState.created = new Date(created).getTime()
  })

  return { stat: initialState, ...groupsDict }
}

/**
 * Unique key for job
 *
 * @param obj {object} - job
 * @returns {string} - unique_key based on full name, job state and related job flags
 *                     e. g. core.account.xxx.job.monitor.SolChild-pending-zombie-wall
 */
function uniqueKey (obj) {
  let value = `${obj.name}-${obj.state}` // core.account.xxx.job.monitor.SolChild-pending

  for (const key in jobFlags) {
    if (obj[key]) value += `-${key}`
  }

  return value // core.account.xxx.job.monitor.SolChild-pending-zombie-wall
}
