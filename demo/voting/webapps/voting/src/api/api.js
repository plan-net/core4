import axios from 'axios'

const addSecretToken = (dto) => {
  return Object.assign({}, dto, {
    token: 'secret_token'
  })
}
export default {
  register (id) {
    return axios
      .post(`/register`, addSecretToken({
        id
      }))
      .then(result => {
        return result.data
      })
      .catch(error => Promise.reject(error.response))
  },
  vote (id) {
    return axios
      .post(`/event`, addSecretToken({
        id,
        data: {
          answer: 'yes'
        }
      })
      )
      .then(result => {
        return result.dataesl
      })
      .catch(error => Promise.reject(error.response))
  }
}
