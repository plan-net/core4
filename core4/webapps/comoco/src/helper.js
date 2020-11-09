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
  const iterator = Array.isArray(iterableObj)
    ? iterableObj
    : Object.keys(iterableObj)
  const value = isFunction(defaultValue) ? defaultValue : clone(defaultValue)

  // !!! clone function returns an empty object in case of
  // !!! cloning object values are functions
  return clone(
    iterator.reduce((computedResult, currentItem) => {
      computedResult[currentItem] = value

      return computedResult
    }, {})
  )

  // return clone(Object.assign(...iterator.map(k => ({ [k]: clone(defaultValue) }))))
}

/**
 * Get base path base on mode: dev or prod
 *
 * @returns {string}
 */
function getBasePath () {
  const isSecure = (location && location.protocol === 'https:') || false

  if (process.env.NODE_ENV === 'development') {
    return isSecure
      ? process.env.VUE_APP_APIBASE_CORE_WSS
      : process.env.VUE_APP_APIBASE_CORE_WS
  } else {
    // production
    return (
      (isSecure ? 'wss://' : 'ws://') +
      `${window.location.host}${process.env.VUE_APP_APIBASE_CORE_WS}`
    )
  }
}

/**
 * Decorator for async/await error flow
 * e.g. [error, success] = await to(<Promise>)
 *
 * @param promise {promise}
 * @returns {Q.Promise<any[]>}
 */
function to (promise) {
  return promise
    .then(data => {
      return [null, data]
    })
    .catch(err => [err])
}

/**
 * Iterable range builder
 *
 * @param from {number}
 * @param to {number}
 * @param reverse {boolean}
 * @returns {object} - iterable object
 */
function range (from, to, reverse) {
  return {
    from: from,
    to: to,

    [Symbol.iterator] () {
      return this
    },

    next () {
      if (reverse) {
        if (this.current === undefined) {
          this.current = this.to
        }

        if (this.current >= this.from) {
          return {
            done: false,
            value: this.current--
          }
        } else {
          delete this.current
          return {
            done: true
          }
        }
      } else {
        if (this.current === undefined) {
          this.current = this.from
        }

        if (this.current <= this.to) {
          return {
            done: false,
            value: this.current++
          }
        } else {
          delete this.current
          return {
            done: true
          }
        }
      }
    }
  }
}

/**
 * Decorator for generator function, make subscribe flow aka Rx approach
 *
 * @param funcGenerator {function}
 * @returns {(function(...[*]): {subscribe: subscribe})}
 */
function subscribeDecorator (funcGenerator) {
  if (!isGenerator(funcGenerator)) {
    console.warn(`Function should be a generator - ${funcGenerator}`)

    return funcGenerator
  }

  if (!window.setImmediate) {
    window.setImmediate = (function () {
      let head = {}
      let tail = head // queue of calls, 1-linked list

      const ID = Math.random() // unique id

      function onmessage (e) {
        if (e.data !== ID) return // not our message
        head = head.next
        const func = head.func
        delete head.func
        func()
      }

      if (window.addEventListener) {
        // IE9+
        window.addEventListener('message', onmessage)
      } else {
        // IE8
        window.attachEvent('onmessage', onmessage)
      }

      return function (func) {
        tail = tail.next = { func: func }
        window.postMessage(ID, '*')
      }
    })()
  }

  const next = (iter, callbacks, prev = undefined) => {
    const { onNext, onErr, onCompleted, unsubscribe } = callbacks
    const item = iter.next(prev)
    const value = item.value

    if (unsubscribe()) {
      // stop chain of calls
      return
    }

    if (item.done) {
      return onCompleted()
    }

    if (isPromise(value)) {
      value.then(
        val => {
          onNext(val)
          setImmediate(() => next(iter, callbacks, val))
        },
        err => {
          onErr(err)
          setImmediate(() => next(iter, callbacks, err))
        }
      )
    } else {
      onNext(value)
      setImmediate(() => next(iter, callbacks, value))
    }
  }

  const gensync = fn => (...args) => ({
    subscribe: (onNext, onErr, onCompleted, unsubscribe) => {
      next(fn(...args), { onNext, onErr, onCompleted, unsubscribe })
    }
  })

  return gensync(funcGenerator)
}

/**
 * Deep merge obj
 *
 * @param target {object} - the object in which we merge
 * @param sources {object} - objects for merge
 *
 * @returns {object} - updated target
 */
function deepMerge (target, ...sources) {
  if (!sources.length) {
    return target
  }

  const source = sources.shift()

  if (source === undefined) {
    return target
  }

  if (isMergebleObject(target) && isMergebleObject(source)) {
    Object.keys(source).forEach(function (key) {
      if (isMergebleObject(source[key])) {
        if (!target[key]) {
          target[key] = {}
        }
        deepMerge(target[key], source[key])
      } else {
        target[key] = source[key]
      }
    })
  }

  return deepMerge(target, ...sources)
}

/**
 * Check is object is a Promise
 *
 * @param obj {object}
 * @returns {boolean}
 */
function isPromise (obj) {
  return Boolean(obj) && typeof obj.then === 'function'
}

/**
 * Check is function is Generator function
 *
 * @param fn {function}
 * @returns {boolean}
 */
function isGenerator (fn) {
  const constructor = fn.constructor

  if (!constructor) return false
  if (constructor.name === 'GeneratorFunction' || constructor.displayName === 'GeneratorFunction') return true

  return isGenerator(constructor.prototype)
}

/**
 * Check is value is a Function
 *
 * @param functionToCheck {any}
 * @returns {boolean}
 */
function isFunction (functionToCheck) {
  return (
    functionToCheck && {}.toString.call(functionToCheck) === '[object Function]'
  )
}

/**
 * Check is value is object
 *
 * @param item {any}
 * @returns {boolean}
 */
function isObject (item) {
  return item !== null && typeof item === 'object'
}

/**
 * Check is value is an empty object
 *
 * @param objectToCheck
 * @returns {boolean}
 */
function isEmptyObject (objectToCheck) {
  return (
    Object.keys(objectToCheck).length === 0 &&
    objectToCheck.constructor === Object
  )
}

/**
 * Check is value is a mergeble object for deepMerge function
 *
 * @param item
 * @returns {boolean}
 */
function isMergebleObject (item) {
  return isObject(item) && !Array.isArray(item)
}

export {
  createObjectWithDefaultValues,
  getBasePath,
  to,
  range,
  isPromise,
  isEmptyObject,
  deepMerge,
  subscribeDecorator
}
