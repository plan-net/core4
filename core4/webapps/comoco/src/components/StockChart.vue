<template>
  <v-layout>
    <v-flex class="chart">
      <vue-highcharts constructor-type="stockChart" :options="chartOptions" ref="chart"></vue-highcharts>
    </v-flex>
  </v-layout>
</template>

<script>
// import moment from 'moment'
import { mapGetters } from 'vuex'

import { Chart } from 'highcharts-vue'
import Highcharts from 'highcharts'
import stockInit from 'highcharts/modules/stock'

import { jobs, jobColors } from '../settings'
import { createObjectWithDefaultValues } from '../helper'

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

export default {
  name: 'stockChart',
  components: {
    VueHighcharts: Chart
  },
  data () {
    return {
      timer: 1000,
      timerId: null,
      isHistoryRetrievingInProgress: true,
      history: createObjectWithDefaultValues(jobs, []),
      recentQueueUpdates: createObjectWithDefaultValues(jobs, [])
    }
  },
  created () {
    // this.$store.dispatch('getChartHistory').then(res => {
    //   console.log('stock chart history: ', res)
    // })
  },
  mounted () { // fired after the element has been created
    if (!this.$refs.chart) return null

    const component = this
    const chart = component.$refs.chart.chart

    let lastHistoryPointTimestamp

    chart.showLoading('Loading data from server...')

    // store actual queue updates while retrieving history
    this.$store.subscribe((mutation, state) => {
      switch (mutation.type) {
        case 'SOCKET_ONMESSAGE':
          if (this.isHistoryRetrievingInProgress && !state.initialState) {
            console.log('recentQueueUpdates', state.event)
            const event = state.event

            jobs.forEach(item => {
              const x = (new Date()).getTime() // current time

              component.recentQueueUpdates[item].push([x, event[item] || 0])
            })
          }
          break
      }
    })

    const onNext = val => {
      console.log(val)
      if (val.data.length) {
        // response from serve sometimes have objects with the same creation date,
        // highchart don't allowed to set points with the same creation date,
        // need to add a 100 milliseconds to creation date so the created key become unique
        val.data.forEach((item, i, arr) => {
          item.timestamp = new Date(item.created).getTime()

          if (item.timestamp === lastHistoryPointTimestamp || item.timestamp < lastHistoryPointTimestamp) {
            arr[i].timestamp = lastHistoryPointTimestamp + 50
          }

          jobs.forEach(job => {
            component.history[job].push([item.timestamp, item[job] || 0])
          })

          lastHistoryPointTimestamp = arr[i].timestamp
        })
      }
    }

    const onCompleted = () => {
      console.log('onCompleted function')
      let last = {}

      const series = chart.series.reduce((computedResult, series) => {
        computedResult[series.name] = series

        return computedResult
      }, {})

      // ToDo: write a comment why it should be like this
      const chartSeriesReference = [
        series.running,
        series.pending,
        series.deferred,
        series.failed,
        series.error,
        series.inactive,
        series.killed
      ]

      component.isHistoryRetrievingInProgress = false

      // add history chunk to chart + recent data from the queue
      chartSeriesReference.forEach(item => {
        const data = component.history[item.name].concat(component.recentQueueUpdates[item.name])

        last[item.name] = data.length ? data[data.length - 1][1] : undefined // ToDo: <--- find better solution

        item.setData(data, false, true, false)
      })

      chart.redraw()
      chart.hideLoading()

      // recursive Timeout easier than Interval for system pressure
      component.timerId = setTimeout(function update () {
        const x = (new Date()).getTime() // current time
        const shift = chart.pointCount > 1750 // (250 points for each series)
        const data = component.isInInitialState ? last : component.getChartData

        chartSeriesReference.forEach(item => {
          item.addPoint([x, data[item.name] || 0], false, shift)
        })

        chart.redraw()

        component.timerId = setTimeout(update, component.timer)
      }, component.timer)
    }

    const onError = (err) => {
      console.log(err.type)
    }

    this.$getChartHistory().subscribe(onNext, onError, onCompleted)
  },
  computed: {
    ...mapGetters(['isInInitialState', 'getChartData']),
    chartOptions () {
      return {
        chart: {
          zoomType: 'x'
        },

        time: {
          useUTC: true
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
        //   adaptToUpdatedData: false
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
            zoom: (e) => { console.log(`zoom, e = `, e) }
          }
          // minRange: 3600 * 1000 // one hour
        },

        series: createSeriesData()
      }
    }
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
