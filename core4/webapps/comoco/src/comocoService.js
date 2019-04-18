import apiService from './apiService.js'
import { to } from './helper'

export class comocoService extends apiService {
  async getChartHistory () {
    let err
    let setting
    let history;

    [err, setting] = await to(this.getSettings('comoco'))
    if (!setting) console.log(err);

    // ToDo: get correct start date

    [err, history] = await to(this.getJobsHistory(/* start date */))
    if (!history) console.log(err)

    return history
  }
}
