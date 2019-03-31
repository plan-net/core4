import state from './state'
import error from './error'
export function setStore (store) {
  store.registerModule('$_state', state)
  store.registerModule('$_error', error)
}
