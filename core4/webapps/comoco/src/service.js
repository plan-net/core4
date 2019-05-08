import moment from 'moment'

import api from './api/index.js'
import { range, subscribeDecorator } from './helper'

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
    Vue.prototype.$getChartHistory = subscribeDecorator(chartHistory)
  }
}

async function getChartHistory (perPage, sort) {
  let setting
  let history

  // ToDo: change to 7 days, check error flow
  let startDate = moment.utc().subtract(60, 'd').format('YYYY-MM-DDTHH:mm:ss')
  let filter = { 'created': { '$gte': startDate } } // mongoDB filter

  try {
    setting = await api.getSetting()

    if (setting.comoco && setting.comoco.startDate) {
      filter['$gte'] = setting.comoco.startDate
    }

    filter = JSON.stringify(filter)

    history = await api.getJobHistory(null, perPage, filter, sort)
  } catch (err) {
    throw Error(err)
  }

  history.startDate = filter

  return history
}

function * chartHistory () {
  let start
  let perPage = 100

  try {
    start = yield getChartHistory(perPage)
  } catch (e) {
    console.log(e)
  }

  for (let page of range(++start.page, --start.page_count)) {
    yield api.getJobHistory(page, perPage, start.startDate)
  }
}
