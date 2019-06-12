<template>
  <v-layout>
    <v-flex class="chart">
      <vue-highcharts constructor-type="stockChart" :options="chartOptions" ref="chart"></vue-highcharts>
    </v-flex>
  </v-layout>
</template>

<script>
import moment from 'moment'
import { mapState } from 'vuex'

import { Chart } from 'highcharts-vue'
import Highcharts from 'highcharts'
import stockInit from 'highcharts/modules/stock'

import { SOCKET_ONMESSAGE } from '../store/comoco.mutationTypes'

import { jobTypes, jobColors } from '../settings'
import { createObjectWithDefaultValues, isEmptyObject } from '../helper'

stockInit(Highcharts)

// var defaultTheme = Highcharts.getOptions()

Highcharts.theme = {
  colors: ['#2b908f', '#90ee7e', '#f45b5b', '#7798BF', '#aaeeee', '#ff0066',
    '#eeaaee', '#55BF3B', '#DF5353', '#7798BF', '#aaeeee'],
  chart: {
    backgroundColor: {
      linearGradient: { x1: 0, y1: 0, x2: 1, y2: 1 },
      stops: [
        [0, '#393939'],
        [1, '#3e3e40']
      ]
    },
    style: {
      fontFamily: '\'Unica One\', sans-serif'
    },
    plotBorderColor: '#606063'
  },

  title: {
    style: {
      color: '#E0E0E3',
      textTransform: 'uppercase',
      fontSize: '20px'
    }
  },

  subtitle: {
    style: {
      color: '#E0E0E3',
      textTransform: 'uppercase'
    }
  },

  xAxis: {
    gridLineColor: '#707073',
    labels: {
      style: {
        color: '#E0E0E3'
      }
    },

    lineColor: '#707073',
    minorGridLineColor: '#505053',
    tickColor: '#707073',
    title: {
      style: {
        color: '#A0A0A3'

      }
    }
  },

  yAxis: {
    gridLineColor: '#707073',
    labels: {
      style: {
        color: '#E0E0E3'
      }
    },
    lineColor: '#707073',
    minorGridLineColor: '#505053',
    tickColor: '#707073',
    tickWidth: 1,
    title: {
      style: {
        color: '#A0A0A3'
      }
    }
  },

  tooltip: {
    backgroundColor: '#282828',
    style: {
      color: '#F0F0F0'
    }
  },

  plotOptions: {
    series: {
      dataLabels: {
        color: '#FFFFFF'
        // color: '#B0B0B3'
      },
      marker: {
        lineColor: '#333'
      }
    },
    boxplot: {
      fillColor: '#505053'
    },
    candlestick: {
      lineColor: 'white'
    },
    errorbar: {
      color: 'white'
    }
  },

  legend: {
    itemStyle: {
      color: '#E0E0E3'
    },
    itemHoverStyle: {
      color: '#FFF'
    },
    itemHiddenStyle: {
      color: '#606063'
    }
  },

  credits: {
    style: {
      color: '#666'
    }
  },

  labels: {
    style: {
      color: '#707073'
    }
  },

  drilldown: {
    activeAxisLabelStyle: {
      color: '#F0F0F3'
    },
    activeDataLabelStyle: {
      color: '#F0F0F3'
    }
  },

  navigation: {
    buttonOptions: {
      symbolStroke: '#DDDDDD',
      theme: {
        fill: '#505053'
      }
    }
  },

  // scroll charts
  rangeSelector: {
    buttonTheme: {
      fill: '#505053',
      stroke: '#000000',
      style: {
        color: '#CCC'
      },
      states: {
        disabled: {
          fill: 'rgba(40,40,40,0.3)',
          stroke: '#000000',
          style: {
            color: 'rgba(255,255,255,0.3)'
          }
        },
        hover: {
          fill: '#707073',
          stroke: '#000000',
          style: {
            color: 'white'
          }
        },
        select: {
          fill: '#282828',
          stroke: '#000000',
          style: {
            color: 'white'
          }
        }
      }
    },
    inputBoxBorderColor: '#505053',
    inputStyle: {
      backgroundColor: '#333',
      color: 'silver'
    },
    labelStyle: {
      color: 'silver'
    }
  },

  navigator: {
    handles: {
      backgroundColor: '#666',
      borderColor: '#AAA'
    },
    outlineColor: '#CCC',
    maskFill: 'rgba(255,255,255,0.1)',
    series: {
      color: '#7798BF',
      lineColor: '#A6C7ED'
    },
    xAxis: {
      gridLineColor: '#505053'
    }
  },

  scrollbar: {
    barBackgroundColor: '#808083',
    barBorderColor: '#808083',
    buttonArrowColor: '#CCC',
    buttonBackgroundColor: '#606063',
    buttonBorderColor: '#606063',
    rifleColor: '#FFF',
    trackBackgroundColor: '#404043',
    trackBorderColor: '#404043'
  },

  // special colors for some of the
  legendBackgroundColor: 'rgba(0, 0, 0, 0.5)',
  background2: '#505053',
  dataLabelsColor: '#B0B0B3',
  textColor: '#C0C0C0',
  contrastTextColor: '#F0F0F3',
  maskColor: 'rgba(255,255,255,0.3)'
}

// Apply the theme
Highcharts.setOptions(Highcharts.theme)

const data = createSeriesData()

export default {
  name: 'stockChart',
  components: {
    VueHighcharts: Chart
  },
  data () {
    return {
      stop: false,
      timer: 1000,
      timerId: null,
      history: createObjectWithDefaultValues(jobTypes, []),
      socketUpdatesCache: createObjectWithDefaultValues(jobTypes, [])
    }
  },
  methods: {
    startStopSwitch (/* status */) {
      this.stop = !this.stop
    }
  },
  created () {},
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
          let msg = state.socket.message

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
      component.$getChartHistory().subscribe(onNext, onError, onCompleted)

      // store actual queue updates while retrieving history
      const socketUpdateUnsubscribe = this.$store.subscribe((mutation, state) => {
        if (socketNotifications[mutation.type]) {
          socketNotifications[mutation.type](state)
        }
      })

      function onNext (value) {
        console.log('on next: ', value)
        if (value.data.length) {
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
    }),
    chartOptions () {
      return {
        chart: {
          zoomType: 'x'
        },

        time: {
          useUTC: false
        },

        rangeSelector: {
          buttons: [{
            count: 1,
            type: 'minute',
            text: '1m'
          },
          {
            count: 5,
            type: 'minute',
            text: '5m'
          },
          {
            count: 10,
            type: 'minute',
            text: '10m'
          },
          {
            count: 30,
            type: 'minute',
            text: '30m'
          },
          {
            type: 'day',
            count: 1,
            text: '1d'
          },
          {
            type: 'all',
            text: 'All'
          }],
          inputEnabled: false,
          selected: 5
        },

        exporting: {
          enabled: false
        },

        tooltip: {
          xDateFormat: '%H:%M:%S | %d-%m-%Y',
          shared: true,
          split: false,
          enabled: true
        },

        // navigator: {
        //   adaptToUpdatedData: false,
        //   series: {
        //     data: data
        //   }
        // },
        //
        // scrollbar: {
        //   liveRedraw: false
        // },

        legend: {
          enabled: true,
          layout: 'horizontal',
          align: 'center',
          verticalAlign: 'bottom',
          borderWidth: 0,
          style: {
            color: '#E0E0E3'
          }
        },

        plotOptions: {
          series: {
            stacking: 'normal',
            showInNavigator: true
          }
        },

        loading: {
          // showDuration: 700,
          hideDuration: 700,
          labelStyle: {
            color: 'white'
          },
          style: {
            backgroundColor: 'gray'
          }
        },

        yAxis: {
          title: {
            text: 'Job count',
            margin: 20
          },
          allowDecimals: false
        },

        xAxis: {
          title: {
            text: 'Time in UTC (Coordinated Universal Time)'
          },
          events: {
            // zoom: (e) => {
            //   console.log(`zoom, e = `, e)
            //   const component = this
            //   const chart = component.$refs.chart.chart
            //
            //   let startDate = moment(e.newMin).format('YYYY-MM-DDTHH:mm:ss')
            //   let endDate = moment(e.newMax).format('YYYY-MM-DDTHH:mm:ss')
            //   let history = createObjectWithDefaultValues(jobTypes, [])
            //
            //   component.$getChartHistory(startDate, endDate).subscribe(onNext, onError, onCompleted)
            //
            //   function onNext (value) {
            //     console.log('on next: ', value)
            //     if (value.data.length) {
            //       // response from serve sometimes have objects with the same creation date,
            //       // highchart don't allowed to set points with the same creation date,
            //       // need to add a 50 milliseconds to creation date so the created key become unique
            //       // this issue should in the future fix on backend side
            //       value.data.forEach(item => {
            //         item.timestamp = new Date(item.created).getTime()
            //
            //         jobTypes.forEach(job => {
            //           // server returns only jobs with a value
            //           // {error: 7, pending: 1, created: "2019-05-21T20:24:05.180000", total: 8}
            //           // need to add rest possible job type with 0 by our self
            //           // {error: 7, pending: 1, running: 0, deferred: 0, failed: 0, inactive: 0, killed: 0}
            //           history[job].push([item.timestamp, item[job] || 0])
            //         })
            //       })
            //     }
            //   }
            //
            //   function onError (e) {
            //     console.log(e)
            //   }
            //
            //   function onCompleted () {
            //     console.log('%c on completed fired function', 'color: green; font-weight: bold;')
            //
            //     const chartSeriesReference = chart.series.reduce((computedResult, series) => {
            //       if (jobTypes.includes(series.name)) {
            //         computedResult.push(series)
            //       }
            //
            //       return computedResult
            //     }, [])
            //
            //     component.startStopSwitch()
            //
            //     // add history chunk + queue cache to chart
            //     chartSeriesReference.forEach(item => {
            //       const zoomHistory = history[item.name]
            //
            //       item.setData(zoomHistory)
            //     })
            //
            //     // chart.redraw()
            //
            //     // component.startStopSwitch()
            //   }
            // }
          }
          // minRange: 3600 * 1000 // one hour
        },

        series: data
      }
    }
  },
  watch: {
    socketReconnectError: 'startStopSwitch'
  },
  beforeDestroy () {
    clearTimeout(this.timerId)
  }
}

// ======================================================================================= //
// Private methods
// ======================================================================================= //

function createSeriesData () {
  let arr = []

  for (let key in jobColors) {
    const color = jobColors[key]

    arr.push({
      name: key,
      color: color,
      type: 'areaspline',
      data: [],
      dataGrouping: {
        enabled: true
      },
      fillColor: {
        linearGradient: {
          x1: 0,
          y1: 0,
          x2: 0,
          y2: 1
        },
        stops: [
          [0, color],
          [1, Highcharts.Color(color).setOpacity(0).get('rgba')]
        ]
      }
    })
  }

  return arr
}

</script>

<style scoped>

</style>
