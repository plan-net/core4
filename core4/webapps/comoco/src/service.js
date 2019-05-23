import moment from 'moment'

import api from './api/index.js'
import { range, subscribeDecorator } from './helper'
import { defaultHistoryRange } from './settings.js'

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

function * chartHistory () {
  let start
  let perPage = 1000

  try {
    start = yield getChartHistory(perPage)

    for (let page of range(++start.page, --start.page_count)) {
      yield api.getJobHistory(page, perPage, start.startDate)
    }
  } catch (e) {
    console.log(e)
  }
}

// ================================================================= //
// Private methods
// ================================================================= //

async function getChartHistory (perPage, sort) {
  let setting
  let history

  // ToDo: change to 7 days, check error flow
  let startDate = moment.utc().subtract(...defaultHistoryRange).format('YYYY-MM-DDTHH:mm:ss')
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
