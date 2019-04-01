/**
 * Detect if the browser is running in Private mode
 *
 * @returns {Promise}
 */

export function isPrivateMode () {
  return new Promise((resolve) => {
    const on = () => resolve(true) // is in private mode
    const off = () => resolve(false) // not private mode
    const testLocalStorage = () => {
      try {
        if (window.localStorage.length) off()
        else {
          window.localStorage.x = 1
          window.localStorage.removeItem('x')
          off()
        }
      } catch (e) {
        // Safari only enables cookie in private mode
        // if cookie is disabled, then all client side storage is disabled
        // if all client side storage is disabled, then there is no point
        // in using private mode
        navigator.cookieEnabled ? on() : off()
      }
    }
    // Chrome & Opera
    if (window.webkitRequestFileSystem) {
      return void window.webkitRequestFileSystem(0, 0, off, on)
    }
    // Firefox
    if ('MozAppearance' in document.documentElement.style) {
      if (window.indexedDB === null) return on()
      const db = window.indexedDB.open('test')
      db.onerror = on
      db.onsuccess = off
      return void 0
    }
    // Safari
    const isSafari = navigator.userAgent.match(/Version\/([0-9\._]+).*Safari/)
    if (isSafari) {
      const version = parseInt(isSafari[1], 10)
      if (version < 11) return testLocalStorage()
      try {
        window.openDatabase(null, null, null, null)
        return off()
      } catch (_) {
        return on()
      }
    }
    // IE10+ & Edge InPrivate
    if (!window.indexedDB && (window.PointerEvent || window.MSPointerEvent)) {
      return on()
    }
    // default navigation mode
    return off()
  })
}
window.PRIVATE_MODE = false
isPrivateMode().then(val => {
  window.PRIVATE_MODE = val
})
