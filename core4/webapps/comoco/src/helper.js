import { clone } from 'core4ui/core4/helper'

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
 * Get base path base on mode: dev or prod
 *
 * @returns {string}
 */
function getBasePath () {
  if (window.location.href.includes('http')) {
    // index.html
    return window.APIBASE_CORE.replace('http:', 'ws:')
  }

  console.error(`incorrect network protocol ${window.location.href}`)

  return `ws://${window.location.host}/core4/api`
}

function to (promise) {
  return promise.then(data => {
    return [null, data]
  })
    .catch(err => [err])
}

export {
  createObjectWithDefaultValues,
  getBasePath,
  to
}
