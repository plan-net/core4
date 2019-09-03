import Vue from 'vue'
import Vuex from 'vuex'
import createLogger from 'vuex/dist/logger'
import api from '@/api'
import { clone } from 'core4ui/core4/helper'
import router from '@/router'

const debug = process.env.NODE_ENV !== 'production'
const plugins = debug ? [createLogger({})] : []

Vue.use(Vuex)

export default new Vuex.Store({
  plugins,
  state: {
    scales: [60, 0.3, 0.6, 0.9],
    searchOptions: {
      technical: false
    },
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
    /*    toggleWidgetListOpen ({
      commit, state
    }, payload) {
      commit('set_widgetlist_open', payload)
    }, */
    updateWidgets ({
      commit
    }, payload) {
      commit('update_widgets', payload)
    },

    async getBoards ({
      dispatch
    }) {
      try {
        const boards = await api.getBoards()
        dispatch('setBoards', boards)
      } catch (err) {

      }
    },
    async enableTechnicalSearch ({
      commit
    }) {
      commit('set_technical_search', true)
    },
    async disableTechnicalSearch ({
      commit
    }) {
      commit('set_technical_search', false)
    },
    async setBoards ({
      commit
    }, boards) {
      if (boards.length) {
        commit('set_boards', boards)
        commit('set_active_board', boards[0].name)
      }
      commit('set_ready', true)
    },
    setActiveBoard ({
      commit,
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
      api.updateBoard({
        boards: getters.boardsSet
      })
    },
    addToBoard ({
      commit,
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
      getters
    }, widgetId) {
      commit('remove_from_board', widgetId)
      const boards = getters.boardsSet
      api.updateBoard({
        boards
      })
    },
    nextBoard ({
      commit,
      getters, state
    }) {
      try {
        const currBoardName = getters.activeBoard.name
        const index = (state.boardsList.indexOf(currBoardName) + 1) % state.boardsList.length
        commit('set_active_board', state.boardsList[index])
      } catch (err) {
        // console.warn(error)
      }
    },
    prevBoard ({
      commit,
      getters, state
    }) {
      try {
        const currBoardName = getters.activeBoard.name
        const prev = (state.boardsList.indexOf(currBoardName) - 1)
        const index = (prev < 0) ? state.boardsList.length - 1 : prev
        commit('set_active_board', state.boardsList[index])
      } catch (err) {
        // console.warn(error)
      }
    },
    setWidgetOver ({
      commit,
      getters
    }, payload) {
      commit('set_widget_over', payload)
    }
  },
  mutations: {
    set_widget_over (state, payload) {
      const widget = clone(state.widgetsObj[payload.id])
      widget.$over = payload.$over
      state.widgetsObj[payload.id] = widget
    },
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
      const board = state.boardsObj[state.activeBoard.name]
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
    set_technical_search (state, value) {
      state.searchOptions.technical = value
    },
    delete_board (state, payload) {
      // Vue.delete(state.boardsObj[payload.name])
      state.boardsList = state.boardsList.filter(val => val !== payload.name)
      state.boardsObj[payload.name] = undefined

      delete state.boardsObj[payload.name]
    },
    set_widgets (state, payload) {
      state.widgetsObj = payload.reduce((obj, item) => {
        obj[item.rsc_id] = item
        return obj
      }, {})
      state.widgetsList = payload.map(val => val.rsc_id)
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
      // return clone(state.widgetsList.map(id => state.widgetsObj[id]))
      const p1 = state.widgetsList.map(id => state.widgetsObj[id])
      if (state.searchOptions.technical === false) {
        return p1.filter(val => {
          return (val.tag || []).includes('api') === false
        })
      }
      return p1
    },
    /*    widgetListOpen (state) {
      return state.widgetListOpen
    }, */
    boardsSet (state) {
      return clone(state.boardsList.map(name => state.boardsObj[name]))
    },
    boardsCount (state) {
      return state.boardsList.length
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
    scales (state) {
      return state.scales
    },
    ready (state) {
      return state.ready
    }
  }
})
