/**
 * General COMOCO config.
 *
 * Existing: job states, job types, job flags, job groups, job colors.
 * Default settings for api calls.
 */

// ToDo: return clones
const defaultHistoryRange = [7, 'd'] // d - in days

const eventChannelNames = [
  'enqueue_job',
  'request_start_job',
  'start_job',
  'failed_start',
  'defer_job',
  'flag_nonstop',
  'flag_zombie',
  'failed_job',
  'inactivate_job',
  'complete_job',
  'request_remove_job',
  'restart_waiting',
  'restart_stopped',
  'request_kill_job',
  'kill_job',
  'remove_job'
]

const jobTypes = ['running', 'pending', 'deferred', 'failed', 'error', 'inactive', 'killed']

const jobColors = {
  pending: '#ffc107',
  deferred: '#f1f128',
  failed: '#11dea2',
  running: '#64a505',
  error: '#d70f14',
  inactive: '#8d1407',
  killed: '#d8c9c7'
}

const jobStates = {
  pending: 'waiting',
  deferred: 'waiting',
  failed: 'waiting',
  running: 'running',
  error: 'stopped',
  inactive: 'stopped',
  killed: 'stopped'
}

const jobFlags = {
  killed: 'k',
  wall: 'n', // nonstop
  removed: 'r',
  zombie: 'z'
}

/**
 * Grouping all job by states
 * e.g. to group "waiting" belongs jobs with state: pending, deferred, failed
 *
 * @param {object} states - dictionary
 *        e.g {<job state>: <group>}
 *
 * @returns {object} - dictionary
 *          e.g. {<jobs group>: [<job state>, ..., <job state>]}
 */
const groupsJobsByStates = (function (states) {
  let result = {}

  for (let key in states) {
    (result[states[key]] = result[states[key]] || []).push(key)
  }

  return result
}(jobStates))

// Array of all existing job groups ['waiting', 'running', 'stopped']
const jobGroups = Object.keys(groupsJobsByStates)

export {
  jobTypes,
  groupsJobsByStates,
  jobStates,
  jobGroups,
  jobFlags,
  jobColors,
  defaultHistoryRange,
  eventChannelNames
}
