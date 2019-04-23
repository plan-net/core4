import apiService from './apiService.js'
import { to } from './helper'

var api = new apiService()

export class comocoService extends apiService {
  async getChartHistory () {
    let err
    let setting
    let history;

    [err, setting] = await to(api.getSettings('comoco'))
    if (!setting) console.log(err)

    try {
      setting = await api.getSettings('comoco')
    } catch (e) {
      console.log(e)
    }

    // ToDo: get correct start date

    [err, history] = await to(api.getJobsHistory(/* start date */))
    if (!history) console.log(err)

    return history
  }
}
