import api from '@/store/api.js'
const state = {
  widgets: [],
  boards: [],
  board: null,
  client: {
    logo: 'targobank-logo.svg'
  }
}

const actions = {
  async initWidgets (context) {
    context.dispatch('fetchBoards')
    await context.dispatch('fetchWidgets')
    return TextTrackCueList
  },
  async fetchBoards (context) {
    const boards = await api.fetchBoards()
    context.commit('setBoards', boards)
    return true
  },
  async fetchWidgets (context) {
    const widgets = await api.fetchWidgets()
    context.commit('setWidgets', widgets)
    return true
  },
  async removeFromBoard (context) {
    console.warn('Not implemnted: removeFromBoard')
  }
}

const mutations = {
  setWidgets (state, payload) {
    state.widgets = payload
  },
  setBoards (state, payload) {
    state.board = payload.board
    state.boards = payload.boards
  }

}

const getters = {
  widgetById: state => id => {
    console.log(id, '------------')
    return state.widgets.find(val => {
      return val.rsc_id === id
    })
  },
  widgets (state) {
    if (state.boards.length && state.widgets.length) {
      const board = state.boards.find(val => val.name === state.board)
      const widgets = state.widgets.filter(val => {
        return board.widgets.includes(val.rsc_id)
      })
      return widgets/* .map(val => {
        return Object.assign(val, {
          width: Math.random() < 0.2 ? 2 : 1,
          height: Math.random() < 0.15 ? 2 : 1
        })
      }) */
    }
    return []
  },
  boards () {
    return state.boards
  },
  board () {
    return state.boards
  }
  /*   busy (state) {
    return state.busy
  },
  tenant (state) {
    return state.tenant
  } */
}
export default {
  namespaced: true,
  state,
  actions,
  mutations,
  getters
}
