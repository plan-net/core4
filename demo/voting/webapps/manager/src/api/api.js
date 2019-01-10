import axios from 'axios'

const addSecretToken = (dto) => {
  return Object.assign({}, dto, { token: 'secret_token' })
}
export default {
  register () {
    return axios
      .post(`/register`, addSecretToken({ id: 'mmr' }))
      .then(result => {
        return result.data
      })
      .catch(error => Promise.reject(error.response))
  },
  fetchQuestions () {
    return axios
      .get(`/session`, { params: addSecretToken({}) })
      .then(result => {
        return result.data
      })
      .catch(error => Promise.reject(error.response))
  },
  fetchResult () {
    return axios
      .post(`/result`, addSecretToken({}))
      .then(result => {
        return result.data
      })
      .catch(error => Promise.reject(error.response))
  },
  saveQuestion (payload) {
    // if new then post, if session_id then put/update
    const method = (payload.session_id == null) ? axios.post : axios.put
    const path = (payload.session_id == null) ? `/session` : `/session/${payload.session_id}`
    return method(path, addSecretToken(payload))
      .then(result => {
        return result.data
      })
      .catch(error => Promise.reject(error.response))
  },
  startQuestion (sessionId) {
    return axios
      .post(`/start/${sessionId}`, addSecretToken({}))
      .then(result => {
        return result.data
      })
      .catch(error => Promise.reject(error.response))
  },
  stopQuestion (sessionId) {
    return axios
      .post(`/stop/${sessionId}`, addSecretToken({}))
      .then(result => {
        return result.data
      })
      .catch(error => Promise.reject(error.response))
  },
  resetQuestion (sessionId) {
    return axios
      .post(`/reset/${sessionId}`, addSecretToken({}))
      .then(result => {
        return result.data
      })
      .catch(error => Promise.reject(error.response))
  },
  dummyVote (payload) {
    return axios
      .post(`/event`, addSecretToken(payload))
      .then(result => {
        return result.data
      })
      .catch(error => Promise.reject(error.response))
  }
}
