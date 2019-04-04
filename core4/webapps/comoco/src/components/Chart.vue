<template>
      <vue-highcharts :options="chartOptions" ref="chart"></vue-highcharts>
</template>

<script>

import { Chart } from 'highcharts-vue'
import Highcharts from 'highcharts'
import streamgraph from 'highcharts/modules/streamgraph'

import { createObjectWithDefaultValues } from "../helper";
import { jobStates } from "../settings";

const chartData = createObjectWithDefaultValues(Object.keys(jobStates), [])

chartData.error = {
  name: 'error',
  color: '#d70f14',
  data: [
    {x: 1554285600000, y: 2}, // 12:00
    {x: 1554286500000, y: 0}, // 12:15

    {x: 1554286560000, y: 22}, // 12:16
    {x: 1554286620000, y: 16}, // 12:17
    {x: 1554286680000, y: 3}, // 12:18
    {x: 1554286740000, y: 0}, // 12:19
    {x: 1554286800000, y: 0}, // 12:20

    {x: 1554287400000, y: 8}, // 12:30

    {x: 1554287580000, y: 10}, // 12:33
    {x: 1554287940000, y: 2}, // 12:39
    {x: 1554288060000, y: 0}, // 12:41

    {x: 1554288300000, y: 25}, // 12:45
    {x: 1554289200000, y: 3} // 13:00
  ]
}

chartData.running = {
  name: 'running',
  color: '#64a505',
  data: [
    {x: 1554285600000, y: 5}, // 12:00
    {x: 1554286500000, y: 0}, // 12:15

    {x: 1554286560000, y: 1}, // 12:16
    {x: 1554286620000, y: 2}, // 12:17
    {x: 1554286680000, y: 3}, // 12:18
    {x: 1554286740000, y: 4}, // 12:19
    {x: 1554286800000, y: 5}, // 12:20


    {x: 1554287400000, y: 9}, // 12:30

    {x: 1554287580000, y: 0}, // 12:33
    {x: 1554287940000, y: 0}, // 12:39
    {x: 1554288060000, y: 0}, // 12:41

    {x: 1554288300000, y: 5}, // 12:45
    {x: 1554289200000, y: 4} // 13:00
  ]
}

Highcharts.theme = {
  chart: {},
  title: {
    enabled: false
  },
  subtitle: {
    enabled: false
  },
  xAxis: {
    labels: {
      style: {
        color: '#E0E0E3'
      }
    }
  },
  yAxis: {
    // gridLineColor: '#707073',
    labels: {
      style: {
        color: '#E0E0E3'
      }
    }
    // lineColor: '#707073',
    // minorGridLineColor: '#505053',
    // tickColor: '#707073',
    // tickWidth: 1,
    // title: {
    //   style: {
    //     color: '#A0A0A3'
    //   }
    // }
  },
  tooltip: {
    backgroundColor: 'rgba(0, 0, 0, 0.85)',
    style: {
      color: '#F0F0F0'
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
  }
}

// Apply the theme
Highcharts.setOptions(Highcharts.theme)

Highcharts.dateFormats = {
  // W: function (timestamp) {
  //   var date = new Date(timestamp)
  //   var day = date.getUTCDay() === 0 ? 7 : date.getUTCDay()
  //   var dayNumber
  //
  //   date.setDate(date.getUTCDate() + 4 - day)
  //   dayNumber = Math.floor((date.getTime() - new Date(date.getUTCFullYear(), 0, 1, -6)) / 86400000)
  //
  //   return 1 + Math.floor(dayNumber / 7)
  // }
}

streamgraph(Highcharts)

export default {
  name: 'JobsStat',
  components: {
    VueHighcharts: Chart
  },
  data () {
    return {
      chartOptions: {
        chart: {
          type: 'streamgraph',
          zoomType: 'x',
          backgroundColor: {
            linearGradient: { x1: 0, y1: 0, x2: 1, y2: 1 },
            stops: [
              [0, '#393939'],
              [1, '#3e3e40']
            ]
          },
          style: {
            fontFamily: '\'Unica One\', sans-serif'
          }
        },

        title: {
          floating: true,
          align: 'left',
          text: 'Queue dashboard'
        },
        legend: {
          enabled: true,
          layout: 'horizontal',
          align: 'left',
          verticalAlign: 'top',
          borderWidth: 0,
          style: {
            color: '#E0E0E3'
          }
        },
        xAxis: {
          type: 'datetime',
          crosshair: true,
          // tickInterval: 1.8e+6, // 30 min
          labels: {
            reserveSpace: false,
            dateTimeLabelFormats: {
              month: '%e. %b',
              year: '%b'
            }
          }
        },
        yAxis: {
          visible: false,
          startOnTick: false,
          endOnTick: false
        },
        // series: [...{chartData}]
        series: [chartData.error, chartData.running]
      }
    }
  }
}
</script>

<style scoped>

</style>
