<template>
  <v-layout>
    <v-flex class="chart" :class="{ 'shadow': !isDark }">
      <vue-highcharts
        constructor-type="stockChart"
        :options="chartOptions"
        ref="chart"
      ></vue-highcharts>
    </v-flex>
  </v-layout>
</template>

<script>
import moment from 'moment'
import { mapState } from 'vuex'
import _ from 'lodash'

import { SOCKET_ONMESSAGE } from '../../store/comoco.mutationTypes'

import { jobTypes, jobColors } from '../../settings'
import { createObjectWithDefaultValues, isEmptyObject } from '../../helper'

import LightTheme from './LightTheme'
import DarkTheme from './DarkTheme'
import ChartOptions from './ChartOptions'
import { Chart } from 'highcharts-vue'
import Highcharts from 'highcharts'
import stockInit from 'highcharts/modules/stock'

stockInit(Highcharts)

export default {
  name: 'stockChart',
  components: {
    VueHighcharts: Chart
  },
  props: {
    isDark: {
      type: Boolean,
      default: false
    }
  },
  data () {
    return {
      stop: false,
      timer: 1000,
      timerId: null,
      history: createObjectWithDefaultValues(jobTypes, []),
      socketUpdatesCache: createObjectWithDefaultValues(jobTypes, []),
      chartOptions: _.merge(this.isDark ? DarkTheme : LightTheme, ChartOptions),
      unsubscribe: false
    }
  },
  methods: {
    startStopSwitch (/* status */) {
      this.stop = !this.stop
    }
  },
  mounted () {
    // fired after the element has been created
    // element might not have been added to the DOM
    this.$nextTick(() => {
      // element has definitely been added to the DOM
      if (!this.$refs.chart) {
        console.log('%c not ready: this.$refs.chart', 'color: red; font-weight: bold;', this.$refs.chart)
      }

      const component = this
      const chart = component.$refs.chart.chart
      const socketNotifications = {
        [SOCKET_ONMESSAGE] (state) {
          const msg = state.socket.message

          if (msg.channel === 'queue' && msg.name !== 'summary') {
            console.log('%c socket updates cache', 'color: orange; font-weight: bold;', state.event)
            const x = (new Date(state.event.created)).getTime()

            jobTypes.forEach(item => {
              component.socketUpdatesCache[item].push([x, state.event[item] || 0])
            })
          }
        }
      }

      chart.showLoading('Loading data from server...')
      // ToDo: subscribe is too complex, rewrite to while loop with async/await
      component.$getChartHistory().subscribe(onNext, onError, onCompleted, unsubscribe)

      // store actual queue updates while retrieving history
      const socketUpdateUnsubscribe = this.$store.subscribe((mutation, state) => {
        if (socketNotifications[mutation.type]) {
          socketNotifications[mutation.type](state)
        }
      })

      function unsubscribe () {
        return component.unsubscribe
      }

      function onNext (value) {
        console.log('on next: ', value)
        if (value.data.length && !component.unsubscribe) {
          // response from serve sometimes have objects with the same creation date,
          // highchart don't allowed to set points with the same creation date,
          // need to add a 50 milliseconds to creation date so the created key become unique
          // this issue should in the future fix on backend side
          value.data.forEach((item, i, arr) => {
            item.timestamp = new Date(item.created).getTime()

            jobTypes.forEach(job => {
              // server returns only jobs with a value
              // {error: 7, pending: 1, created: "2019-05-21T20:24:05.180000", total: 8}
              // need to add rest possible job type with 0 by our self
              // {error: 7, pending: 1, running: 0, deferred: 0, failed: 0, inactive: 0, killed: 0}
              component.history[job].push([item.timestamp, item[job] || 0])
            })
          })
        }
      }

      function onError (err) {
        // ToDo: cover this case
        console.log('%c on error', 'color: red; font-weight: bold;', err.type)
      }

      function onCompleted () {
        console.log('%c on completed fired function', 'color: green; font-weight: bold;')

        const chartSeriesReference = chart.series.reduce((computedResult, series) => {
          if (jobTypes.includes(series.name)) {
            computedResult.push(series)
          }

          return computedResult
        }, [])

        socketUpdateUnsubscribe()

        // add history chunk + queue cache to chart
        chartSeriesReference.forEach(item => {
          const history = component.history[item.name].concat(component.socketUpdatesCache[item.name])

          item.setData(history, false, true, false)
        })

        chart.redraw()
        chart.hideLoading()

        // recursive Timeout easier than Interval for system pressure
        component.timerId = setTimeout(function update () {
          // move chart every second in case of chart not in stop mode and
          // we already have received first chunk of data from server
          if (!component.stop && !isEmptyObject(component.getChartData)) {
            const data = component.getChartData
            const x = (new Date(moment.utc().format('YYYY-MM-DDTHH:mm:ss'))).getTime() // current time
            const shift = chart.pointCount > 1750 // (250 points for each series)

            chartSeriesReference.forEach(item => {
              item.addPoint([x, data[item.name]], false, shift)
            })

            chart.redraw()
          }

          component.timerId = setTimeout(update, component.timer)
        }, component.timer)
      }
    })
  },
  computed: {
    ...mapState({
      getChartData: (state) => state.event,
      socketReconnectError: (state) => state.socket.reconnectError
    })
  },
  watch: {
    socketReconnectError: 'startStopSwitch'
  },
  beforeDestroy () {
    this.unsubscribe = true
    clearTimeout(this.timerId)
  }
}
</script>

<style scoped>
.shadow {
  box-shadow: 0 3px 1px -2px rgba(0,0,0,.2), 0 2px 2px 0 rgba(0,0,0,.14), 0 1px 5px 0 rgba(0,0,0,.12);
}
</style>
