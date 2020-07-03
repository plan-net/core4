const state = {
  stockChartVisible: true
}

const actions = {

  toggleChartVis (context) {
    context.commit('setChart', !context.state.stockChartVisible)
  },
  showChart (context) {
    context.commit('setChart', true)
  },
  hideChart (context) {
    context.commit('setChart', false)
  }
}

const mutations = {
  setChart (state, payload) {
    state.stockChartVisible = payload
  }
}

const getters = {
  stockChartVisible (state) {
    return state.stockChartVisible
  }
}
export default {
  namespaced: true,
  state,
  actions,
  mutations,
  getters
}
