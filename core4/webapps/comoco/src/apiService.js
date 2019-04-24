import { axiosInternal } from 'core4ui/core4/internal/axios.config.js'

// const API_URL = environment.apiUrl;

export default {
  getSetting (query) {
    const path = query ? `/setting/${query}` : `/setting`

    return axiosInternal
      .get(path)
      .then(result => result.data)
      .catch(error => Promise.reject(error))
  },

  getJobHistory (start) {
    let token = JSON.parse(localStorage.getItem('user'))['token']

    return axiosInternal
      .get(`v1/jobs/history?token=${token}`)
      .then(result => result.data)
      .catch(error => Promise.reject(error))
  }
}
// import { axiosInternal } from 'core4ui/core4/internal/axios.config.js'
//
// // const API_URL = environment.apiUrl;
//
// export default {
//   install (Vue, options) {
//     // ES6 way of const job = options.job
//     // const { <name> } = options
//
//     Vue.prototype.$getSetting = getSetting
//     Vue.prototype.$getJobHistory = getJobHistory
//   }
// }
//
// function getSetting (query) {
//   const path = query ? `/setting/${query}` : `/setting`
//
//   return axiosInternal
//     .get(path)
//     .then(result => result.data)
//     .catch(error => Promise.reject(error))
// }
//
// function getJobHistory (start) {
//   let token = JSON.parse(localStorage.getItem('user'))['token']
//
//   return axiosInternal
//     .get(`v1/jobs/history?token=${token}`)
//     .then(result => result.data)
//     .catch(error => Promise.reject(error))
// }
