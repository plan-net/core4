import api from './api/index.js'
import { to } from './helper'

export default {
  install (Vue, options) {
    // ES6 way of const job = options.job
    // const { <name> } = options
    const serverAPI = api

    // extend with default server API
    for (let method in serverAPI) {
      Vue.prototype[`$${method}`] = serverAPI[method]
    }

    // extend with custom API
    Vue.prototype.$getChartHistory = getChartHistory
  }
}

async function getChartHistory () {
  let err
  let setting
  let history
  // let startDate

  // [err, setting] = await to(api.getSetting('comoco'))
  // if (!setting) console.log(err)

  try {
    setting = await api.getSetting()
  } catch (e) {
    console.log(e)
  }

  // ToDo: get correct start date
  [err, history] = await to(api.getJobHistory(/* start date */))
  if (!history) console.log(err)

  return history
}
