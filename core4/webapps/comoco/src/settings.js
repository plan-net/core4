/**
 * General jobs config. Existing job states, existing job flags, existing job groups
 */

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
  groupsJobsByStates,
  jobStates,
  jobGroups,
  jobFlags
}
