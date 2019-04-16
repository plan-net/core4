<template>
  <v-layout>
    <v-flex class="chart">
      <vue-highcharts constructor-type="stockChart" :options="chartOptions" ref="chart"></vue-highcharts>
    </v-flex>
  </v-layout>
</template>

<script>
import { mapGetters } from 'vuex'

import { Chart } from 'highcharts-vue'
import Highcharts from 'highcharts'
import stockInit from 'highcharts/modules/stock'

import { jobColors } from '../settings'

stockInit(Highcharts)

var defaultTheme = Highcharts.getOptions()

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
      timerId: undefined
    }
  },
  mounted () { // fired after the element has been created
    if (!this.$refs.chart) return null

    const component = this
    const chart = component.$refs.chart.chart

    // ToDo: write a comment why it should be like this
    const running = chart.series[0]
    const pending = chart.series[1]
    const deferred = chart.series[2]
    const failed = chart.series[3]
    const error = chart.series[4]
    const inactive = chart.series[5]
    const killed = chart.series[6]

    const arr = [running, pending, deferred, failed, error, inactive, killed]

    component.timerId = setTimeout(function update () {
      const x = (new Date()).getTime()// current time
      const shift = running.length > 3600 // 1 hour

      if (component.getChartData) {
        arr.forEach(item => {
          item.addPoint([x, component.getChartData[item.name]], false, shift)
        })

        chart.redraw()
      }

      component.timerId = setTimeout(update, component.timer)
    }, component.timer)
  },
  computed: {
    ...mapGetters(['getChartData']),
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
            type: 'hour',
            count: 1,
            text: '1h'
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
          }
        },

        series: createSeriesData()
      }
    }
  },
  beforeDestroy () {
    clearTimeout(this.timerId)
  }
}

// ================================================================= //
// Private methods
// ================================================================= //

function createSeriesData () {
  let arr = []

  for (let key in jobColors) {
    const color = jobColors[key]

    arr.push({
      name: key,
      color: color,
      type: 'areaspline',
      data: [],
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
