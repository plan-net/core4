import axios from 'axios'
const SECRET = 'fguusdifhsk'

let API = './'
export function setCookieConfig (_api) {
  API = _api
}
export default {
  getCookieDate (params) {
    const now = new Date()
    const date = new Date(Date.UTC(now.getFullYear(), now.getMonth(), now.getDate(), now.getHours(), now.getMinutes(), now.getSeconds()))
    return date
  },
  optIn (data) {
    return axios
      .put(`${API}/optin`, data)
      .then(result => result)
      .catch(error => Promise.reject(error.response))
  },

  setPriPolCookie () {
    const date = new Date()
    date.setTime(date.getTime() + (28 * 24 * 60 * 60 * 1000))
    const expires = '; expires=' + date.toUTCString()
    document.cookie = SECRET + '=' + this.getCookieDate() + expires + '; path=/'
  },

  isPriPolCookieSet () {
    const nameEQ = SECRET + '='
    const ca = document.cookie.split(';')
    for (let i = 0; i < ca.length; i++) {
      let c = ca[i]
      while (c.charAt(0) === ' ') {
        c = c.substring(1, c.length)
      }
      if (c.indexOf(nameEQ) === 0) {
        return c.substring(nameEQ.length, c.length)
      }
    }
    return false
  }

}
