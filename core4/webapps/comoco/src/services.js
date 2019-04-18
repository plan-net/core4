import { axiosInternal } from 'pnbi-base/core4/internal/axios.config.js'

export default {
  settings (query) {
    const path = query ? `/setting/${query}` : `/setting`

    return axiosInternal
      .get(path)
      .then(result => {
        return result.data
      })
      .catch(error => {
        return Promise.reject(error)
      })
  },
  history (start) {
    let token = JSON.parse(localStorage.getItem('user'))['token']

    return axiosInternal
      .get(`v1/jobs/history?token=${token}`)
      .then(result => {
        return result.data
      })
      .catch(error => {
        return Promise.reject(error)
      })
  }
}
