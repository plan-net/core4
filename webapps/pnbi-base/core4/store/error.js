const state = {
  error: null
}

const actions = {
  showError ({ commit }, payload) {
    console.warn(payload)
    commit('show_error', payload)
  },
  hideError ({ commit, dispatch }) {
    commit('hide_error')
    dispatch('setLoading', false)
  }
}

const mutations = {
  show_error (state, payload) {
    state.error = payload
  },
  hide_error (state, payload) {
    state.error = null
  }
}

const getters = {
  error (state) {
    return state.error
  }
}

export default {
  state,
  actions,
  mutations,
  getters
}
