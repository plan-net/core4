import { axiosInternal } from 'core4ui/core4/internal/axios.config.js'

// const API_URL = environment.apiUrl;

export default {
  getWidgets () {
    return axiosInternal
      .get(`/info`, { params: { per_page: 1000, page: 0 } })
      .then(result => result.data)
      .catch(error => Promise.reject(error.response))
  },

  getSetting (query) {
    const url = query ? `/setting/${query}` : `/setting`

    return axiosInternal
      .get(url)
      .then(result => result.data)
      .catch(error => Promise.reject(error))
  },

  getJobHistory (page, perPage, filter) {
    let token = JSON.parse(localStorage.getItem('user'))['token']
    let pageArg = page ? `page=${page}` : ''
    let perPageArg = perPage ? `&per_page=${perPage}` : ''
    let filterArg = filter ? `&filter=${filter}` : ''

    return axiosInternal
      .get(`/jobs/history?${pageArg}${perPageArg}${filterArg}&token=${token}`)
      .then(res => {
        return {
          total_count: res.total_count,
          page: res.page,
          per_page: res.per_page,
          page_count: res.page_count,
          data: res.data
        }
      })
      .catch(error => Promise.reject(error))
  }
}
