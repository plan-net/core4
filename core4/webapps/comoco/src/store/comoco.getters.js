import { clone } from 'core4ui/core4/helper'
import { jobGroups } from '../settings'

export default {
  ...mapGettersJobGroups(jobGroups), // getter for each job type (pending, deferred, ..., killed)
  getJobsByGroupName: (state, getters) => (groupName) => getters[groupName],
  getStateCounter: (state) => (stateName) => {
    if (state.queue.stat === undefined) return 0

    return stateName.reduce((previousValue, currentItem) => {
      previousValue += state.queue.stat[currentItem] || 0

      return previousValue
    }, 0)
  }
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
    computedResult[currentItem] = (state) => {
      return clone(state.queue[currentItem] || [])
    }

    return computedResult
  }, {})
}
