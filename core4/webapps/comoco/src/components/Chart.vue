<template>
  <div>
    <vue-highcharts :options="chartOptions" :updateArgs="[true, true, { duration: 1000}]" ref="chart"></vue-highcharts>
<!--    <vue-highcharts :options="chartOptions" :updateArgs="updateArgs" ref="chart"></vue-highcharts>-->
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import { Chart } from 'highcharts-vue'
import Highcharts from 'highcharts'
import streamgraph from 'highcharts/modules/streamgraph'

streamgraph(Highcharts)

// Highcharts.theme = {
//   chart: {},
//   title: {
//     enabled: false
//   },
//   subtitle: {
//     enabled: false
//   },
//   xAxis: {
//     labels: {
//       style: {
//         color: '#E0E0E3'
//       }
//     }
//   },
//   yAxis: {
//     // gridLineColor: '#707073',
//     labels: {
//       style: {
//         color: '#E0E0E3'
//       }
//     }
//     // lineColor: '#707073',
//     // minorGridLineColor: '#505053',
//     // tickColor: '#707073',
//     // tickWidth: 1,
//     // title: {
//     //   style: {
//     //     color: '#A0A0A3'
//     //   }
//     // }
//   },
//   tooltip: {
//     backgroundColor: 'rgba(0, 0, 0, 0.85)',
//     style: {
//       color: '#F0F0F0'
//     }
//   },
//   legend: {
//     itemStyle: {
//       color: '#E0E0E3'
//     },
//     itemHoverStyle: {
//       color: '#FFF'
//     },
//     itemHiddenStyle: {
//       color: '#606063'
//     }
//   }
// }
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

  xAxis: {
    gridLineColor: '#707073',
    labels: {
      style: {
        color: '#E0E0E3'
      }
    },
    lineColor: '#707073',
    minorGridLineColor: '#505053',
    tickColor: '#707073'
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
    tickWidth: 1
  },
  tooltip: {
    backgroundColor: 'rgba(0, 0, 0, 0.85)',
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
  rangeSelector: {
    buttonTheme: {
      fill: '#505053',
      stroke: '#000000',
      style: {
        color: '#CCC'
      },
      states: {
        hover: {
          fill: '#707073',
          stroke: '#000000',
          style: {
            color: 'white'
          }
        },
        select: {
          fill: '#000003',
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
  name: 'JobsStat',
  components: {
    VueHighcharts: Chart
  },
  data () {
    return {
      pointOnPlot: 5
    }
  },
  watch: {
    getChartData: {
      handler (val) {
        if (!this.$refs.chart) return null

        let chart = this.$refs.chart.chart

        const running = chart.series[0]
        const pending = chart.series[1]
        const deferred = chart.series[2]
        const failed = chart.series[3]
        const error = chart.series[4]
        const inactive = chart.series[5]
        const killed = chart.series[6]
        const arr = [running, pending, deferred, failed, error, inactive, killed]

        const shift = running.data.length > 100 // ToDo: 7 days history
        const x = (new Date()).getTime()

        arr.forEach((item) => {
          item.addPoint([x, val[item.name]], false, shift)
        })

        chart.redraw()
      },
      deep: true
    }
  },
  computed: {
    ...mapGetters(['getChartData']),
    shift () {
      if (this.$refs.chart && this.$refs.chart.chart.series.data[0]) {
        return this.$refs.chart.chart.series.data[0] > this.pointOnPlot
      } else {
        return false
      }
    },
    chartOptions () {
      return {
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
        xAxis: {
          title: {
            text: 'Time in UTC (Coordinated Universal Time)',
            margin: 30
          },
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
        plotOptions: {
          area: {
            stacking: 'normal'
          },
          series: {
            showInNavigator: true
          }
        },

        yAxis: {
          title: {
            text: 'Job count',
            margin: 20
          },
          allowDecimals: false
        },

        rangeSelector: {
          buttons: [{
            count: 1,
            type: 'minute',
            text: '1M'
          }, {
            count: 5,
            type: 'minute',
            text: '5M'
          }, {
            type: 'hour',
            count: 1,
            text: '1h'
          }, {
            type: 'all',
            text: 'All'
          }],
          inputEnabled: false,
          selected: 3
        },

        series: [
          {
            name: 'pending',
            type: 'streamgraph',
            color: '#ffc107',
            data: [[(new Date()).getTime(), 0]]
          },
          {
            name: 'deferred',
            type: 'streamgraph',
            color: '#f1f128',
            data: [[(new Date()).getTime(), 0]]
          },
          {
            name: 'failed',
            type: 'streamgraph',
            color: '#11dea2',
            data: [[(new Date()).getTime(), 0]]
          },
          {
            name: 'running',
            type: 'streamgraph',
            color: '#64a505',
            data: [[(new Date()).getTime(), 0]]
          },
          {
            name: 'error',
            type: 'streamgraph',
            color: '#d70f14',
            data: [[(new Date()).getTime(), 0]]
          },
          {
            name: 'inactive',
            type: 'streamgraph',
            color: '#8d1407',
            data: [[(new Date()).getTime(), 0]]
          },
          {
            name: 'killed',
            type: 'streamgraph',
            color: '#d8c9c7',
            data: [[(new Date()).getTime(), 0]]
          }
        ]
      }
    }
  }
}
</script>

<style scoped>

</style>
