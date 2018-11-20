/* import sim from '@/api/sim' */
import { clone } from 'pnbi-base/src/helper'
import Api from '@/api/api'
import Vue from 'vue'
import axios from 'axios'
// import router from '@/router.js'
const state = {
  sse: null,
  questions: [],
  current: null,
  results: null,
  result: null
}

const actions = {
  dummyVote ({ commit, dispatch, getters }, sid) {
    // const current = getters.question
    Api.dummyVote({ id: Math.random() * Math.random() })
  },
  fetchQuestions ({ commit, dispatch, getters }, sid) {
    Api.fetchQuestions().then(val => {
      commit('set_questions', val)
      if (sid != null) {
        dispatch('setCurrentQuestion', { session_id: sid })
      }
      const qs = getters.questions
      qs.forEach(val => {
        if (val.state === 'OPEN') {
          dispatch('stopQuestion', val)
        }
      })
    })
  },
  fetchResult ({ commit, dispatch, getters }, sid) {
    Api.fetchResult().then(val => {
      commit('set_result', val)
      if (sid != null) {
        /*         const result = val.filter(val2 => {
          console.log(val2.session_id)
          return val2.session_id === sid
        })
        console.log(result)
        commit('set_current_result', result) */
        dispatch('setCurrentResult', { session_id: sid })
      } else {
        try {
          dispatch('setCurrentResult', { session_id: val[0].session_id })
        } catch (err) {}
      }
    })
  },
  setCurrentResult ({ commit, getters }, payload) {
    const result = getters.results.filter(val => val.session_id === payload.session_id)
    console.log(result, payload, '#############')
    commit('set_current_result', result)
  },
  saveQuestion ({ commit, dispatch }, payload) {
    Api.saveQuestion(payload).then(val => {
      dispatch('showNotification', {
        text: 'Die Frage wurde gespeichert.'
      }, { root: true })
      dispatch('fetchQuestions')
    })
  },
  startQuestion ({ commit, dispatch, getters }, payload) {
    const next = payload || getters.question
    Api.startQuestion(next.session_id).then(val => {
      commit('set_current_question', val)
      const path = (`${axios.defaults.baseURL}/poll/${next.session_id}?token=secret_token`).replace('//poll', '/poll')
      Vue.SSE(path, { format: 'json' })
        .then(sse => {
          commit('set_server_side_events', sse)
          dispatch('showNotification', {
            text: `Die Frage "${payload.question}" wurde gestartet.`
          }, { root: true })
          sse.onError(e => {
            console.error('lost connection; giving up!', e)
            sse.close()
          })
          sse.subscribe('', message => {
            const seconds = (new Date(message.timestamp).getTime() - new Date(getters.question.started_at).getTime()) / 1000
            console.log(Object.assign(message, { seconds }))
            commit('update_current_question', Object.assign(message, { seconds }))
          })
        })
        .catch(err => {
          console.warn(err)
          dispatch('fetchQuestions', next.session_id)
        })
    })
  },
  stopQuestion ({ commit, dispatch, getters }, payload) {
    const next = payload || getters.question
    Api.stopQuestion(next.session_id).then(val => {
      try {
        getters.sse.close()
      } catch (err) {}
      dispatch('showNotification', {
        text: `Die Frage "${next.question}" wurde gestoppt.`
      }, { root: true })
      commit('update_current_question', { state: 'CLOSED' })
      // commit('set_current_question', null)
    }).catch(err => {
      console.error('Failed to connect to server', err)
    })
  },
  updateCurrentQuestion ({ commit, getters }, payload) {
    commit('update_current_question', payload)
  },
  setCurrentQuestion ({ commit, getters }, payload) {
    if (payload && payload.session_id != null) {
      const current = getters.questions.find(val => val.session_id === payload.session_id)
      commit('set_current_question', current)
    } else {
      commit('set_current_question', null)
    }
  }
}

const mutations = {
  set_server_side_events (state, payload) {
    state.sse = payload
  },
  set_questions (state, payload) {
    state.questions = payload
  },
  set_result (state, payload) {
    state.results = payload
  },
  set_current_result (state, payload) {
    state.result = payload
  },
  set_current_question (state, payload) {
    state.current = payload
  },
  update_current_question (state, payload) {
    const next = Object.assign({}, clone(state.current), payload)
    state.current = next
  }
}

const getters = {
  sse (state) {
    return state.sse
  },
  questions (state) {
    return state.questions
  },
  question (state) {
    return state.current
  },
  results (state) {
    return state.results
  },
  result (state) {
    return state.result
  }
}

export default {
  state,
  actions,
  mutations,
  getters
}
