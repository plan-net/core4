import Vue from 'vue'
import Vuex from 'vuex'
import createLogger from 'vuex/dist/logger'
import api from '@/api'
import {
  clone
} from 'pnbi-base/core4/helper'
import router from '@/router'
Vue.use(Vuex)

export default new Vuex.Store({
  plugins: [createLogger()],
  state: {
    widgetsObj: {},
    widgetsList: [],

    boardsObj: {},
    boardsList: [],

    ready: false,
    activeBoard: {
      name: null,
      widgets: []
    }
  },
  actions: {
    async getWidgets ({
      commit,
      dispatch
    }) {
      dispatch('setLoading', true)
      const widgets = await api.getWidgets()
      commit('set_widgets', widgets)
      dispatch('setLoading', false)
    },
    updateWidgets ({
      commit,
      dispatch
    }, payload) {
      commit('update_widgets', payload)
    },

    async getBoards ({
      commit,
      dispatch
    }) {
      const boards = await api.getBoards()
      dispatch('setBoards', boards)
    },
    async setBoards ({
      commit,
      dispatch
    }, boards) {
      if (boards.length) {
        commit('set_boards', boards)
        commit('set_active_board', boards[0].name)
      }
      commit('set_ready', true)
    },
    setActiveBoard ({
      commit,
      dispatch,
      getters
    }, name) {
      if (name) {
        commit('set_active_board', name)
      } else {
        const boards = getters.boardsSet
        commit('set_active_board', boards[0].name)
      }
      router.push('/')
    },
    async createBoard ({
      commit,
      dispatch,
      getters
    }, board) {
      try {
        await api.createBoard({
          board,
          boards: getters.boardsSet
        })
        commit('add_board', board)
        window.setTimeout(function () {
          commit('set_active_board', board.name)
        }, 500)
      } catch (err) {
        console.log(err)
      }
    },
    async updateBoard ({
      commit,
      dispatch,
      getters
    }, name) {
      commit('update_board_name', name)
      api.updateBoard({
        boards: getters.boardsSet
      })
    },
    updateBoardWidgets ({
      commit,
      dispatch,
      getters
    }, widgets) {
      commit('update_board_widgets', widgets)
      api.updateBoard({
        boards: getters.boardsSet
      })
    },
    deleteBoard ({
      commit,
      dispatch,
      getters,
      state
    }, board) {
      commit('delete_board', board)
      commit('set_active_board', state.boardsList[0])
      /* if (state.activeBoard.name === board.name) {
        const index = state.boardsList.indexOf(board.name)
        let active = 0
        if (index < state.boardsList.length - 1) {
          active = index + 1
        }
        if (state.boardsList.length > 1) {
          commit('set_active_board', state.boardsList[active])
        } else {
          commit('set_active_board', null)
        }
      }
 */
      api.updateBoard({
        boards: getters.boardsSet
      })
    },
    addToBoard ({
      commit,
      dispatch,
      getters
    }, widgetId) {
      const board = getters.activeBoard
      if (board.widgets.includes(widgetId)) {
        return
      }
      commit('add_to_board', widgetId)
      const boards = getters.boardsSet
      api.updateBoard({
        boards
      })
    },
    removeFromBoard ({
      commit,
      dispatch,
      getters
    }, widgetId) {
      commit('remove_from_board', widgetId)
      const boards = getters.boardsSet
      api.updateBoard({
        boards
      })
    }
  },
  mutations: {
    set_boards (state, payload) {
      state.boardsObj = payload.reduce((obj, item) => {
        obj[item.name] = item
        return obj
      }, {})
      state.boardsList = payload.map(val => val.name)
    },
    add_board (state, payload) {
      state.boardsObj = Object.assign(state.boardsObj, {
        [payload.name]: payload
      })
      state.boardsList.push(payload.name)
    },
    set_active_board (state, payload) {
      try {
        state.activeBoard = state.boardsObj[payload]
      } catch (err) {
        state.activeBoard = {
          name: null,
          widgets: []
        }
      }
    },
    update_board_widgets (state, widgets) {
      state.boardsObj[state.activeBoard.name].widgets = widgets
      state.activeBoard.widgets = widgets
    },
    update_board_name (state, name) {
      const board = state.boardsObj[state.activeBoard]
      board.name = name
    },
    add_to_board (state, widgetId) {
      const elem = clone(state.activeBoard)
      if (elem.widgets.includes(widgetId) === false) {
        elem.widgets.push(widgetId)
        state.boardsObj[state.activeBoard.name] = elem
        state.activeBoard = elem
      }
    },
    remove_from_board (state, widgetId) {
      const elem = clone(state.activeBoard)
      elem.widgets = elem.widgets.filter(id => {
        return id !== widgetId
      })
      state.boardsObj[state.activeBoard.name] = elem
      state.activeBoard = elem
    },
    delete_board (state, payload) {
      // Vue.delete(state.boardsObj[payload.name])
      state.boardsList = state.boardsList.filter(val => val !== payload.name)
      state.boardsObj[payload.name] = undefined

      delete state.boardsObj[payload.name]
    },
    set_widgets (state, payload) {
      state.widgetsObj = payload.reduce((obj, item) => {
        obj[item._id] = item
        return obj
      }, {})
      state.widgetsList = payload.map(val => val._id)
    },
    set_ready (state, payload) {
      state.ready = payload
    }
  },
  getters: {
    widgetById: state => id => {
      return state.widgetsObj[id]
    },
    widgetsList (state) {
      return state.widgetsList
    },
    widgetSet (state) {
      return clone(state.widgetsList.map(id => state.widgetsObj[id]))
    },
    boardsSet (state) {
      return clone(state.boardsList.map(name => state.boardsObj[name]))
    },
    boards (state) {
      return state.boardsObj
    },
    activeBoard (state) {
      if ((state.activeBoard || {}).name != null) {
        return clone(state.activeBoard)
      }
      return null
    },
    ready (state) {
      return state.ready
    }
  }
})
