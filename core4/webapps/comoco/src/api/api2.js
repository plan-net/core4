import axios from 'axios'
import Vue from 'vue'
import { SSE } from '@/components/misc/sse.modified.js'

const on = () => {}
const off = () => {}
export function getSSE (
  options = { endpoint: 'jobs/poll', json: {} }
) {
  const path = `${process.env.VUE_APP_APIBASE_CORE}/${options.endpoint}` // token necessary here because stream handling
  return new SSE(path, {
    headers: { 'Content-Type': 'text/plain' },
    payload: JSON.stringify(options.json) // dont touch, or sse will become GET ...
  })
}

const ApiService = {
  errorHandlerCaught (error = null) {
    const errorDetail = error.response.data
    let ret = false
    if (errorDetail.code === 403) {
      Vue.prototype.raiseError(error)
      ret = true
    }
    return ret
  },
  async get (resource) {
    on()
    try {
      const ret = await axios.get(resource)
      return ret
    } catch (err) {
      if (ApiService.errorHandlerCaught(err) === false) {
        throw err
      }
    } finally {
      off()
    }
  },

  async post (resource, data) {
    on()
    try {
      const ret = await axios.post(resource, data)
      return ret
    } catch (err) {
      if (ApiService.errorHandlerCaught(err) === false) {
        throw err
      }
    } finally {
      off()
    }
  },

  async put (resource, data) {
    on()
    try {
      const ret = await axios.put(resource, data)
      return ret
    } catch (err) {
      if (ApiService.errorHandlerCaught(err) === false) {
        throw err
      }
    } finally {
      off()
    }
  },

  async delete (resource) {
    on()
    try {
      const ret = await axios.delete(resource)
      return ret
    } catch (err) {
      if (ApiService.errorHandlerCaught(err) === false) {
        throw err
      }
    } finally {
      off()
    }
  },

  customRequest (data) {
    return axios(data)
  }
}

export default ApiService
