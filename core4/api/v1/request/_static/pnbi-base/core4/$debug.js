export function notImplemented (name) {
  return new Promise((resolve, reject) => {
    reject(new Error(`${name}: not implemented`))
  })
}

export default {
  notImplemented
}
