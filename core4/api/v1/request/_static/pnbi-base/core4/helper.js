export function clone (element) {
  try {
    element = JSON.parse(JSON.stringify(element))
  } catch (err) {
    console.error(err)
  }
  return element
}
export function flatten (arr) {
  return [].concat.apply([], arr)
}
export function unique (arr) {
  return [...new Set(arr)]
}
export function removeDollar (obj) {
  const isObj = myVar => {
    return myVar !== null && typeof myVar === 'object'
  }
  for (const key in obj) {
    if (key.indexOf('$') === 0) {
      delete obj[key]
    } else if (isObj(obj[key])) {
      removeDollar(obj[key])
    }
  }
  return obj
}
export function camelize (str) {
  return str
    .replace(/(?:^\w|[A-Z]|\b\w)/g, (letter, index) => {
      return index === 0 ? letter.toLowerCase() : letter.toUpperCase()
    })
    .replace(/\s+/g, '')
}
export function pad (n, width, z = '0') {
  n = String(n)
  return n.length >= width ? n : new Array(width - n.length + 1).join(z) + n
}
export function deepFreeze (o) {
  Object.freeze(o)

  Object.getOwnPropertyNames(o).forEach(function (prop) {
    if (
      o.hasOwnProperty(prop) &&
      o[prop] !== null &&
      (typeof o[prop] === 'object' || typeof o[prop] === 'function') &&
      !Object.isFrozen(o[prop])
    ) {
      deepFreeze(o[prop])
    }
  })
  return o
}
export default {
  flatten,
  unique,
  removeDollar,
  camelize,
  pad,
  clone,
  deepFreeze
}
