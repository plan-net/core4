import axios from 'axios'
export const instance = axios.create({
  baseURL: process.env.VUE_APP_APIBASE_CORE,
  headers: {
    common: { Accept: 'application/json' }
  }

})
