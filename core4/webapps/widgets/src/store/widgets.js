import api from '@/store/api.js'
import router from '@/router'
import { axiosInternal } from 'core4ui/core4/internal/axios.config.js'
import _ from 'lodash'
// import Vue from 'vue'
let ti
const state = {
  widgetsWaitingRoom: [],
  widgets: [],
  boards: null,
  board: null,
  client: {
    logo: 'targobank-logo.svg'
  }
}

const actions = {
  async initApp (context) {
    await context.dispatch('fetchBoards')
    // await context.dispatch('fetchWidgets')
    return true
  },
  async fetchBoards (context) {
    window.clearTimeout(ti)
    const boards = await api.fetchBoards()
    context.commit('setBoards', boards.boards)
    //  wait for route params
    ti = window.setTimeout(function () {
      context.dispatch('setActiveBoard', boards.board)
    }, 25)
    return boards.boards
  },
  /*   async searchWidgets (context) {
    console.log('searchWidgets', '-------')
  }, */
  async removeFromBoard (context, widgetId) {
    context.commit('removeFromBoard', widgetId)
    await api.updateBoard({
      boards: context.state.boards
    })
    /*     const boards = getters.boardsSet
    api.updateBoard({
      boards
    }) */
  },
  setActiveBoard (context, board) {
    context.commit('setActiveBoard', board)
    context.dispatch('fetchWidgets')
    if (router.history.current.params.board !== board) {
      router.push({ name: 'Home', params: { board } })
    }
    return true
  },
  fetchWidgets (context) {
    /*     if ((context.state.boards == null || context.state.boards.length = 0)) {
      throw new Error("No boards available");
    } */
    const boardComplete = context.state.boards.find(
      val => val.name === context.state.board
    )
    boardComplete.widgets.forEach(val => {
      if (typeof (val) === 'string') {
        context.dispatch('fetchWidget', val)
      } else {
        console.warn('Not implmented yet: widget is obj')
      }
    })
  },
  async fetchWidget (context, id) {
    try {
      const widget = await axiosInternal.get(
        `_info/card/${id}`,
        { headers: { common: { Accept: 'application/json' } } }
      )
      const type = typeof widget
      if (type === 'string') {
        // html
        context.commit('preAddWidget', {
          rsc_id: id,
          html: widget
        })
      } else {
        // json
        context.commit('preAddWidget', widget)
      }
    } catch (error) {
      context.commit('preAddWidget', {
        rsc_id: id,
        error
      })
      // console.log('NotFound', this.widget)
    }
    const boardComplete = context.state.boards.find(
      val => val.name === context.state.board
    )

    if (context.state.widgetsWaitingRoom.length === boardComplete.widgets.length) {
      // all widgets loaded
      const w = _.cloneDeep(context.state.widgetsWaitingRoom)
      // sort like saved
      const w2 = boardComplete.widgets.map(val => {
        return w.find(val2 => val2.rsc_id === val)
      })
      context.commit('setWidgets', w2)
    }
    return true
  },

  async createBoard ({ commit, getters, state }, dto) {
    // try {
    const exists = state.boards.find(val => val.name === dto.board)
    if (exists != null) {
      throw new Error('Board exists')
    } else {
      const nb = {
        name: dto.board,
        widgets: []
      }
      const boards = (state.boards || []).concat([nb])
      await api.createBoard(boards)
      commit('add_board', nb)
    }
  },
  async updateBoard (context, delta) {
    // const boardWithWidgets = _.cloneDeep(context.getters.boardWithWidgets)
    const flat = delta.map(val => val.rsc_id)
    const obj = {}
    flat.forEach(val => {
      obj[flat] = delta.filter(val2 => val2.rsc_id === val)
    })
    console.log(flat, obj)
    /*     boardWithWidgets.widgets = boardWithWidgets.widgets.map(val => {
      if(val.rsc_id)
    })  */
  }
}

const mutations = {
  preAddWidget (state, widget) {
    const widgetAdded = state.widgetsWaitingRoom.findIndex(val => val.rsc_id === widget.rsc_id)
    if (widgetAdded >= 0) {
      state.widgetsWaitingRoom.splice(widgetAdded, 1, widget)
    } else {
      state.widgetsWaitingRoom = state.widgetsWaitingRoom.concat([widget])
    }
  },
  removeFromBoard (state, id) {
    state.boards = state.boards.map(
      val => {
        if (val.name === state.board) {
          val.widgets = val.widgets.filter(val2 => val2 !== id)
        }
        return val
      }
    )
  },
  setWidgets (state, payload) {
    state.widgets = payload
  },
  setBoards (state, payload) {
    state.boards = payload
  },
  setActiveBoard (state, payload) {
    state.board = payload
  }
}

const getters = {
  widgetById: state => id => {
    return state.widgets.find(val => {
      return val.rsc_id === id
    })
  },
  widgets (state) {
    /* if (state.boards.length && state.widgets.length) {
      const board = state.boards.find(val => val.name === state.board)
      const widgets = state.widgets.filter(val => {
        return board.widgets.includes(val.rsc_id)
      })
      return widgets
    }
    return [] */
    return state.widgets
  },
  boards () {
    return state.boards
  },
  board () {
    return state.board
  },
  boardWithWidgets () {
    return state.boards.find(val => val.name === state.board)
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
