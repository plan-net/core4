import { axiosInternal } from 'core4ui/core4/internal/axios.config.js'

// const API_URL = environment.apiUrl;

export default {
  getWidgets () {
    return axiosInternal
      .get('/info', { params: { per_page: 1000, page: 0 } })
      .then(result => result.data)
      .catch(error => Promise.reject(error.response))
  },

  getSetting (query) {
    const url = query ? `/setting/${query}` : '/setting'

    return axiosInternal
      .get(url)
      .then(result => result.data)
      .catch(error => Promise.reject(error))
  },

  getQueueHistory (page, perPage, startDate, endDate, sort) {
    const token = JSON.parse(localStorage.getItem('user')).token
    const pageArg = page ? `page=${page}` : ''
    const perPageArg = perPage ? `&perPage=${perPage}` : ''
    const startDateArg = startDate ? `&startDate=${startDate}` : ''
    const endDateArg = endDate ? `&endDate=${endDate}` : ''
    const sortArg = sort ? `&sort=${sort}` : '&sort=1'

    return axiosInternal
      .get(
        `/queue/history?${pageArg}${perPageArg}${startDateArg}${endDateArg}${sortArg}&token=${token}`
      )
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
