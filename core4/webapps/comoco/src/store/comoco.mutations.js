import Vue from 'vue'

import {
  SOCKET_ONOPEN,
  SOCKET_ONCLOSE,
  SOCKET_ONERROR,
  SOCKET_ONMESSAGE,
  SOCKET_RECONNECT,
  SOCKET_RECONNECT_ERROR,
  ERROR_CHANGE_STATE
} from './comoco.mutationTypes'

import { createObjectWithDefaultValues } from '../helper'
import { jobTypes, jobFlags, jobStates, eventChannelNames } from '../settings'

const defaultEventObj = createObjectWithDefaultValues(jobTypes, 0)
const channelDict = {
  'queue': {
    // on_queue:
    'summary': queueChannelHandler,
    // on_event:
    ...eventChannelNames.reduce((computedResult, currentItem) => {
      computedResult[currentItem] = eventChannelHandler

      return computedResult
    }, {})
  }
}

console.log(createObjectWithDefaultValues(eventChannelNames, eventChannelHandler))

export default {
  [SOCKET_ONOPEN] (state, event) {
    Vue.prototype.$socket = event.currentTarget
    Vue.prototype.$socket.sendObj({ 'type': 'interest', 'data': ['queue', 'event'] })
    state.socket.isConnected = true
    state.error.socket_reconnect_error.state = false
  },
  [SOCKET_ONCLOSE] (state) {
    state.socket.isConnected = false
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
    state.socket.reconnectError = true
    state.error.socket_reconnect_error.state = true
    state.error.socket_reconnect_error.type = 'error'
    // state.error.message = 'Cannot connect to the serve.'
    state.error.socket_reconnect_error.slot = 'socketReconnectError'
    state.stopChart = true
  },
  [ERROR_CHANGE_STATE] (state, payload) {
    state.error[payload.errType].state = payload.stateValue
  }
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
  console.log('queue', message)
  state.queue = groupDataAndJobStat(message.created, message.data, 'state')

  if (state.stopChart) {
    state.event = state.queue.stat
  }

  state.stopChart = false
}

/**
 * Handler for event notification
 *
 * @param state {object} - store state
 * @param message {object} - ws notification
 */
function eventChannelHandler (state, message) {
  console.log('event', message)
  state.event = { ...defaultEventObj, ...message.data.queue }
  state.event['created'] = message.created
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
  let groupsDict = {}
  let initialState = createObjectWithDefaultValues(jobStates)

  arr.forEach((job) => {
    if (!job.key) job.key = uniqueKey(job)

    let jobState = job[groupingKey]
    let group = jobStates[jobState] || 'other';

    (groupsDict[group] = groupsDict[group] || []).push(job)

    initialState[jobState] += job['n']
    initialState['created'] = (new Date(created)).getTime()
  })

  return { 'stat': initialState, ...groupsDict }
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

  for (let key in jobFlags) {
    if (obj[key]) value += `-${key}`
  }

  return value // core.account.xxx.job.monitor.SolChild-pending-zombie-wall
}
