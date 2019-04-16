import axios from 'axios'
import router from './routes/index.js'
import Vue from 'vue'

export const axiosInternal = axios.create({
  baseURL: window.APIBASE_CORE
})

axios.defaults.baseURL = window.APIBASE_APP

export function setAjaxConfig (config) {
  // helpers
  const ingnoredErrors = config.IGNORED_ERRORS || []

  function isIgnoredEndopoint (responseURL = '') {
    return ['/login', '/logout', '/profile', '/settings'].find(val => {
      return responseURL.includes(val)
    }) != null
  }
  function isErrorIgnoreRoute () {
    return router.publicPages.includes(router.instance.history.current.path)
  }
  function isIgnoredError (error) {
    // app can defined errors which willl be handled by app
    let val = false
    try {
      val = ingnoredErrors.includes(error.response.status)
    } catch (err) {

    }
    return val
  }
  function isErrorCode (error, type) {
    return error.response.status === type
  }

  function showError (data) {
    const mute = isIgnoredEndopoint(data.error.response.request.responseURL)
    if (mute) {
      // no error dialog, just do nothing
      return false
    }
    const errors = {
      '403': `${Vue.prototype.i18n.t('errors.isPermissionsError')} <a href="mailto:mail@mailer.com">mail@mailer.com</a>`,
      '500': `${Vue.prototype.i18n.t('errors.is500Error')} <a href="mailto:mail@mailer.com">mail@mailer.com</a>`
    }
    const dto = {
      status_code: data.error.response.status
    }
    if (data.json != null) {
      dto.json = data.json
    } else {
      dto.html = errors[data.error.response.status]
    }
    Vue.prototype.$store.dispatch('showError', dto)
  }
  // AXIOS //
  // used in pnbi-base client
  // used internally by Auth.js because Auth Path is different then api above
  const instances = [axios, axiosInternal]
  instances.forEach(axiosInstance => {
    axiosInstance.defaults.headers.common['Accept'] = 'application/json'
    axiosInstance.interceptors.response.use(
      response => {
        return response.data
      },
      error => {
        if (isIgnoredError(error) === false) {
          if (isErrorCode(error, 401)) {
            const shouldRedirectToLogin = isErrorIgnoreRoute() === false
            if (shouldRedirectToLogin) {
              Vue.prototype.$store.dispatch('gotoLogin')
            }
          } else if (isErrorCode(error, 403)) {
            showError({ error })
          } else if (isErrorCode(error, 500)) {
            showError({ error })
          } else {
            showError({
              error,
              json: (error.response.data || error.response)
            })
          }
        }
        const loading = Vue.prototype.$store.getters.loading
        if (loading) {
          Vue.prototype.$store.dispatch('setLoading', false)
        }
        return Promise.reject(error.response.data)
      }
    )
    axiosInstance.interceptors.request.use(
      request => {
        if (request.url.includes('/login') === false) {
          const user = JSON.parse(window.localStorage.getItem('user'))
          if (user != null) {
            request.headers.Authorization = `Bearer ${user.token}`
          }
        }
        return request
      },
      error => {
        return Promise.reject(error)
      }
    )
  })
}
