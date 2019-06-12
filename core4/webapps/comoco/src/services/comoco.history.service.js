import moment from 'moment'

import api from '../api'
import { range, subscribeDecorator } from '../helper'
import { defaultHistoryRange } from '../settings.js'

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

function * chartHistory (startDate, endDate) {
  let start
  let perPage = 1000

  try {
    start = yield getChartHistory(perPage, 1, startDate, endDate)

    for (let page of range(++start.page, --start.page_count)) {
      yield api.getJobHistory(page, perPage, start.startDate, start.endDate)
    }
  } catch (e) {
    console.log(e)
  }
}

// ================================================================= //
// Private methods
// ================================================================= //

// async function getChartHistory (perPage, sort) {
//   let setting
//   let history
//   let startDate = moment.utc().subtract(...defaultHistoryRange).format('YYYY-MM-DDTHH:mm:ss')
//   let filter = { 'created': { '$gte': startDate } } // mongoDB filter
//
//   try {
//     setting = await api.getSetting()
//
//     if (setting.comoco && setting.comoco.startDate) {
//       filter['$gte'] = setting.comoco.startDate
//     }
//
//     filter = JSON.stringify(filter)
//
//     history = await api.getJobHistory(null, perPage, filter, sort)
//   } catch (err) {
//     throw Error(err)
//   }
//
//   history.startDate = filter
//
//   return history
// }

async function getChartHistory (perPage, sort, startDate, endDate) {
  let setting
  let history

  try {
    if (!startDate) {
      setting = await api.getSetting()

      if (setting.comoco && setting.comoco.startDate) {
        startDate = moment(setting.comoco.startDate).format('YYYY-MM-DDTHH:mm:ss')
      }
    // else {
    //     startDate = moment.utc().subtract(...defaultHistoryRange).format('YYYY-MM-DDTHH:mm:ss') // mongoDB filter
    //   }
    }

    if (endDate) {
      endDate = moment(endDate).format('YYYY-MM-DDTHH:mm:ss') // mongoDB filter
    }

    history = await api.getJobHistory(null, perPage, startDate, endDate, sort)
  } catch (err) {
    throw Error(err)
  }

  history.startDate = startDate
  history.endDate = endDate

  return history
}
