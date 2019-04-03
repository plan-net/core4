import { clone } from 'pnbi-base/core4/helper'

/**
 * Create object with defined keys with default value for each key
 *
 * @param {object|array} iterableObj - [<key 1>, ..., <key n>]
 * @param {any} defaultValue
 *
 * @returns obj - object with default value
 *                e. g. {<key 1>: <defaultValue>, <key n>: <defaultValue>}
 */
function createObjectWithDefaultValues (iterableObj, defaultValue = 0) {
  let iterator = Array.isArray(iterableObj) ? iterableObj : Object.keys(iterableObj)

  return clone(Object.assign(...iterator.map(k => ({ [k]: clone(defaultValue) }))))
}

/**
 * Get host name by window location
 *
 * @returns {string}
 */
const getBasePath = () => {
  if (window.location.href.includes('http')) {
    // index.html
    return window.APIBASE_CORE.replace('http:', 'ws:')
  }

  return `ws://${window.location.hostname}${window.APIBASE_CORE}`
}

export {
  createObjectWithDefaultValues,
  getBasePath
}
