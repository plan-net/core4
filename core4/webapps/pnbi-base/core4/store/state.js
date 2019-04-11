import Auth from '../Auth'
import bus from '../event-bus.js'
// import CookieService from '../internal/cookie.service.js'
import router from '../internal/routes/index.js'
import { axiosInternal } from '../internal/axios.config.js'

const state = {
  hasOwnTheme: false,
  loading: false,
  dark: false,
  title: 'CORE4OS',
  notification: null,

  profile: {
    error: null,
    // cookie: CookieService.isPriPolCookieSet(),
    authenticated: false,
    name: null,
    email: 'No email',
    short: 'NA'
  }
}

const actions = {
  showNotification ({ commit }, payload) {
    bus.$emit('SHOW_NOTIFICATION', payload)
  },
  fetchProfile ({ commit, dispatch, getters }, payload) {
    const promiseProfile = Auth.profile()
    const promiseSetting = Auth.setting()
    Promise.all([promiseProfile, promiseSetting])
      .then(data => {
        const profile = data[0]
        const setting = data[1]
        const dto = {
          authenticated: true,
          name: profile.name,
          realname: profile.realname,
          email: profile.email,
          short: profile.short,
          perm: profile.perm,
          role: profile.role
        }
        commit('set_profile', dto)
        if (getters.hasOwnTheme === false) {
          commit('set_dark', setting.dark)
        }

        if (router.instance.history.current.name === 'login') {
          dispatch('gotoStart')
        }
      }, () => {
        // commit('set_profile', { error: 'auth' })
      })
  },
  gotoStart ({ commit, dispatch }) {
    commit('clear_auth_error')
    commit('set_profile', { authenticated: true })
    dispatch('fetchProfile')
    router.instance.push('/')
  },
  gotoLogin ({ commit }) {
    window.localStorage.removeItem('user')
    commit('clear_profile')
    router.instance.push('/login')
  },
  checkLogin ({ commit, dispatch }, payload) {
    const user = JSON.parse(window.localStorage.getItem('user'))
    if (user != null) {
      Auth.login(user).then(val => {
        dispatch('gotoStart')
      }).catch(() => {
        dispatch('gotoLogin')
        commit('set_profile', { error: 'auth' })
      })
    }
  },
  login ({ commit, dispatch }, payload) {
    return new Promise((resolve, reject) => {
      Auth.login(payload).then(result => {
        resolve(true)
        dispatch('gotoStart')
      }).catch((err) => {
        console.log(err.response, 'Login.Error')
        commit('set_profile', { error: 'auth' })
        reject(new Error('LoginError'))
        return Promise.reject(err)
      })
    })
  },
  logout ({ commit, dispatch }, payload) {
    Auth.logout().then(function () {
      dispatch('gotoLogin')
    }).catch((err) => {
      dispatch('gotoLogin')
      return Promise.reject(err)
    })
  },
  clearAuthError ({ commit }) {
    commit('clear_auth_error')
  },
  setLoading ({ commit }, payload) {
    commit('set_loading', payload)
  },
  setTitle ({ commit }, payload) {
    commit('set_title', payload)
    document.title = payload
    document.querySelector('body').classList.add(payload.toLowerCase().split(' ').join('-'))
  },
  initializeApp ({ commit, dispatch }, payload) {
    dispatch('setTitle', payload.TITLE)
    if (payload.DARK != null) {
      commit('set_dark', payload.DARK)
      state.hasOwnTheme = true // do not show theme switch
    }
  },
  toggleDark ({ commit, getters }) {
    const dark = !getters.dark
    commit('set_dark', dark)
    return axiosInternal
      .post('/setting/_general', { data: { dark } })
      .then(result => {
      })
      .catch(error => Promise.reject(error))
  }
}

const mutations = {
  set_notification (state, payload) {
    state.notification = payload
  },
  set_dark (state, dark) {
    if (dark != null) {
      state.dark = dark
    }
  },
  clear_auth_error () {
    delete state.profile.error
  },
  set_profile (state, payload) {
    if (payload.authenticated === true) {
      delete state.profile.error
    }
    state.profile = Object.assign({}, state.profile, payload)
  },
  clear_profile (state, payload) {
    state.profile = {
      // cookie: CookieService.isPriPolCookieSet(),
      authenticated: false,
      name: null
    }
  },
  set_loading (state, payload) {
    state.loading = payload
  },
  set_title (state, payload) {
    state.title = payload
  },
  initialize_app (state, payload) {
    state.title = payload.title
  }
}

const getters = {
  profile (state) {
    return state.profile
  },
  authenticated (state) {
    return state.profile.authenticated
  },
  loading (state) {
    return state.loading
  },
  title (state) {
    return state.title
  },
  dark (state) {
    return state.dark
  },
  hasOwnTheme (state) {
    return state.hasOwnTheme
  }
}

export default {
  state,
  actions,
  mutations,
  getters
}
