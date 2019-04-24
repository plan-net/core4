import api from './apiService.js'
import { to } from './helper'

// export default {
//   async getChartHistory () {
//     let err
//     let setting
//     let history;
//
//     [err, setting] = await to(api.getSetting('comoco'))
//     if (!setting) console.log(err)
//
//     try {
//       setting = await api.getSettings('comoco')
//     } catch (e) {
//       console.log(e)
//     }
//
//     // ToDo: get correct start date
//     [err, history] = await to(api.getJobHistory(/* start date */))
//     if (!history) console.log(err)
//
//     return history
//   }
// }

export default {
  install (Vue, options) {
    // ES6 way of const job = options.job
    // const { <name> } = options

    Vue.prototype.$getChartHistory = getChartHistory
  }
}

async function getChartHistory () {
  let err
  let setting
  let history;

  // [err, setting] = await to(api.getSetting('comoco'))
  // if (!setting) console.log(err)

  try {
    setting = await api.getSettings('comoco')
  } catch (e) {
    console.log(e)
  }

  // ToDo: get correct start date
  [err, history] = await to(api.getJobHistory(/* start date */))
  if (!history) console.log(err)

  return history
}
