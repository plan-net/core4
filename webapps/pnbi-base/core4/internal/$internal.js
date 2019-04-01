export function shortName (rn) {
  let short = null
  if (rn.includes(' ')) {
    short = rn.split(' ').map(val => val.charAt(0).toUpperCase()).join('')
  } else {
    short = rn.substring(0, 1)
  }
  return short
}
export function unwrapMessage (object) {
  if (object.data.result.message != null) {
    return object.data.result.message
  }
  return object.data
}

export default {
  shortName
}
