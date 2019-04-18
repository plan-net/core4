import { axiosInternal } from 'pnbi-base/core4/internal/axios.config.js'

// const API_URL = environment.apiUrl;

export class ApiService {
  // constructor (name) {}

  getSettings (query) {
    const path = query ? `/setting/${query}` : `/setting`

    return axiosInternal
      .get(path)
      .then(result => result.data)
      .catch(error => Promise.reject(error))
  }

  getJobsHistory (start) {
    let token = JSON.parse(localStorage.getItem('user'))['token']

    return axiosInternal
      .get(`v1/jobs/history?token=${token}`)
      .then(result => result.data)
      .catch(error => Promise.reject(error))
  }
}
// export default {
//   settings (query) {
//     const path = query ? `/setting/${query}` : `/setting`
//
//     return axiosInternal
//       .get(path)
//       .then(result => result.data)
//       .catch(error => Promise.reject(error))
//   },
//   history (start) {
//     let token = JSON.parse(localStorage.getItem('user'))['token']
//
//     return axiosInternal
//       .get(`v1/jobs/history?token=${token}`)
//       .then(result => result.data)
//       .catch(error => Promise.reject(error))
//   }
// }
