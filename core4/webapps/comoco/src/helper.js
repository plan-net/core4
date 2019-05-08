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
  return promise
    .then(data => {
      return [null, data]
    })
    .catch(err => [err])
}

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

function isPromise (obj) {
  return Boolean(obj) && typeof obj.then === 'function'
}

function isGenerator (fn) {
  return fn.constructor.name === 'GeneratorFunction'
}

function subscribeDecorator (funcGenerator) {
  if (!isGenerator(funcGenerator)) {
    console.warn(`Function ${funcGenerator} should be generator`)

    return funcGenerator
  }

  if (!window.setImmediate) {
    window.setImmediate = (function () {
      let head = {}
      let tail = head // очередь вызовов, 1-связный список

      let ID = Math.random() // unique id

      function onmessage (e) {
        if (e.data !== ID) return // не наше сообщение
        head = head.next
        let func = head.func
        delete head.func
        func()
      }

      if (window.addEventListener) { // IE9+
        window.addEventListener('message', onmessage)
      } else { // IE8
        window.attachEvent('onmessage', onmessage)
      }

      return function (func) {
        tail = tail.next = { func: func }
        window.postMessage(ID, '*')
      }
    }())
  }

  const next = (iter, callbacks, prev = undefined) => {
    const { onNext, onCompleted } = callbacks
    const item = iter.next(prev)
    const value = item.value

    if (item.done) {
      return onCompleted()
    }

    if (isPromise(value)) {
      value.then(val => {
        onNext(val)
        setImmediate(() => next(iter, callbacks, val))
      })
    } else {
      onNext(value)
      setImmediate(() => next(iter, callbacks, value))
    }
  }

  const gensync = (fn) => (...args) => ({
    subscribe: (onNext, onError, onCompleted) => {
      next(fn(...args), { onNext, onError, onCompleted })
    }
  })

  return gensync(funcGenerator)
}

export {
  createObjectWithDefaultValues,
  getBasePath,
  to,
  range,
  isPromise,
  subscribeDecorator
}
