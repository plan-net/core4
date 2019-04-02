import { axiosInternal } from 'pnbi-base/core4/internal/axios.config.js'

export default {
  getWidgets () {
    return axiosInternal
      .get(`/info`, { params: { per_page: 1000, page: 0 } })
      .then(result => {
        return result.data
      })
      .catch(error => Promise.reject(error.response))
  }
}
