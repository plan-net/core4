import Vue from 'vue'
import Vuex from 'vuex'
import createLogger from 'vuex/dist/logger'
import api from '@/api'
import { clone } from 'core4ui/core4/helper'
import router from '@/router'
export function notify (dispatch, message) {
  if (typeof message === 'string') {
    message = {
      text: message,
      type: 'success'
    }
  }
  if (message.text == null) {
    return
  }
  message.timeout = message.timeout || 5000
  dispatch('showNotification', message)
}

const debug = process.env.NODE_ENV !== 'production'
const plugins = debug ? [createLogger({})] : []

Vue.use(Vuex)

export default new Vuex.Store({
  plugins,
  state: {
    scales: [60, 0.3, 0.6, 0.9],
    currScale: 0.3,
    currScaleAbs: 400,
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
    async getWidgets ({ commit, dispatch }) {
      dispatch('setLoading', true)
      const widgets = await api.getWidgets()
      commit('set_widgets', widgets)
      dispatch('setLoading', false)
    },
    updateWidgets ({ commit }, payload) {
      commit('update_widgets', payload)
    },
    setCurrScale ({ commit, state }, dto = { index: 1, persist: true }) {
      if (dto.index == null) {
        dto.index = 1
      }
      if (dto.index > 0) {
        const bodyW = document.querySelector('body').offsetWidth
        const scaleAbs = bodyW * state.scales[dto.index]
        commit('set_curr_scale_abs', scaleAbs)
      }
      commit('set_curr_scale', state.scales[dto.index])

      if (dto.persist === true) {
        try {
          api.persistOptions({ sidebar: dto.index })
        } catch (err) {}
      }
    },
    async getBoards ({ dispatch }) {
      try {
        const boards = await api.getBoards()
        dispatch(
          'setOptions',
          boards
        ) /* { boards: [], board: 'name', sidebar: 1 } */
      } catch (err) {}
    },
    async enableTechnicalSearch ({
      commit
    }) {
      try {
        api.persistOptions({ technical: true })
      } catch (err) {}
      commit('set_technical_search', true)
    },
    async disableTechnicalSearch ({
      commit
    }) {
      api.persistOptions({ technical: false })
      commit('set_technical_search', false)
    },
    async setOptions ( // setConfig
      { commit, dispatch },
      dto = {
        boards: [],
        board: '',
        sidebar: 0,
        technical: false

      }
    ) {
      if (dto.boards.length) {
        commit('set_boards', dto.boards)
        const boardExists =
          (dto.boards.find(val => val.name === dto.board) || {}).name ||
          dto.boards[0].name
        commit('set_active_board', boardExists)
      }
      if (dto.technical === true) {
        dispatch('enableTechnicalSearch')
      } else {
        dispatch('disableTechnicalSearch')
      }
      dispatch('setCurrScale', { index: (dto.sidebar), persist: false })
      commit('set_ready', true)
    },

    setActiveBoard ({ commit, dispatch, getters }, name) {
      if (name == null) {
        const boards = getters.boardsSet
        name = boards[0].name
      }
      commit('set_active_board', name)
      try {
        api.persistOptions({ board: name })
      } catch (err) {}
      router.push('/')
    },
    async createBoard ({ commit, getters }, board) {
      try {
        await api.createBoard({
          board,
          boards: getters.boardsSet
        })
        commit('add_board', board)
        window.setTimeout(function () {
          commit('set_active_board', board.name)
        }, 500)
      } catch (err) {}
    },
    async updateBoard ({ commit, dispatch, getters }, name) {
      commit('update_board_name', name)
      api.updateBoard({
        boards: getters.boardsSet
      })
    },
    updateBoardWidgets ({ commit, getters }, widgets) {
      commit('update_board_widgets', widgets)
      api.updateBoard({
        boards: getters.boardsSet
      })
    },
    deleteBoard ({ commit, dispatch, getters, state }, board) {
      commit('delete_board', board)
      commit('set_active_board', state.boardsList[0])
      api.updateBoard({
        boards: getters.boardsSet
      })
    },
    addToBoard ({ commit, getters }, widgetId) {
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
    removeFromBoard ({ commit, getters }, widgetId) {
      commit('remove_from_board', widgetId)
      const boards = getters.boardsSet
      api.updateBoard({
        boards
      })
    },
    nextBoard ({ commit, getters, state }) {
      try {
        const currBoardName = getters.activeBoard.name
        const index =
          (state.boardsList.indexOf(currBoardName) + 1) %
          state.boardsList.length
        const name = state.boardsList[index]
        commit('set_active_board', name)
        api.persistOptions({ board: name })
      } catch (err) {
        // console.warn(error)
      }
    },
    prevBoard ({ commit, getters, state }) {
      try {
        const currBoardName = getters.activeBoard.name
        const prev = state.boardsList.indexOf(currBoardName) - 1
        const index = prev < 0 ? state.boardsList.length - 1 : prev
        const name = state.boardsList[index]
        commit('set_active_board', name)
        api.persistOptions({ board: name })
      } catch (err) {
        // console.warn(error)
      }
    },
    setWidgetOver ({ commit }, payload) {
      commit('set_widget_over', payload)
    },
    clear ({ commit }) {
      commit('clear')
    }

  },
  mutations: {
    clear (state) {
      state = Object.assign({}, {
        scales: [60, 0.3, 0.6, 0.9],
        currScale: 0.3,
        currScaleAbs: 400,
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
      })
    },
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
    set_curr_scale (state, scale) {
      state.currScale = scale
    },
    set_curr_scale_abs (state, scale) {
      state.currScaleAbs = scale
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
    },
    currScalePerc (state) {
      return state.currScale
    },
    currScaleAbs (state) {
      return state.currScaleAbs
    },
    searchOptions (state) {
      return state.searchOptions
    }
  }
})
