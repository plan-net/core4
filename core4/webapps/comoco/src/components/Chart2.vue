<template>
      <vue-highcharts constructor-type="stockChart" :options="chartOptions" ref="chart"></vue-highcharts>
</template>

<script>
import { mapGetters } from 'vuex'
import { Chart } from 'highcharts-vue'
import Highcharts from 'highcharts'
import stockInit from 'highcharts/modules/stock'
stockInit(Highcharts)
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
    backgroundColor: 'rgba(0, 0, 0, 0.85)',
    style: {
      color: '#F0F0F0'
    }
  },
  plotOptions: {
    series: {
      dataLabels: {
        color: '#B0B0B3'
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
};

// Apply the theme
Highcharts.setOptions(Highcharts.theme)

export default {
  name: 'JobsStat2',
  components: {
    VueHighcharts: Chart
  },
  data () {
    return {

    }
  },
  watch: {
    getChart: {
      handler: function (val, oldVal) {
        if (!this.$refs.chart) {
          return null
        }

        let chart = this.$refs.chart.chart
        var running = chart.series[0]
        var pending = chart.series[1]
        var deferred = chart.series[2]
        var failed = chart.series[3]
        var error = chart.series[4]
        var inactive = chart.series[5]
        var killed = chart.series[6]
        var arr = [running, pending, deferred, failed, error, inactive, killed]

        var shift = pending.data.lenght > 10
        var x = (new Date()).getTime()// current time

        arr.forEach((item) => {
          item.addPoint([x, Math.round(Math.random() * 200)], false, shift, { duration: 1000 })
        })

        chart.redraw()
      },
      deep: true
    }
  },
  computed: {
    ...mapGetters(['getChart']),
    chartOptions () {
      return {
        chart: {
          events: {
            load: function () {

              // set up the updating of the chart each second
              // var chart = this
              // var running = this.series[0]
              // var pending = this.series[1]
              // var deferred = this.series[2]
              // var failed = this.series[3]
              // var error = this.series[4]
              // var inactive = this.series[5]
              // var killed = this.series[6]
              // var arr = [running, pending, deferred, failed, error, inactive, killed]
              //
              // var shift = pending.data.lenght > 10
              //
              // setInterval(function () {
              //   var x = (new Date()).getTime()// current time
              //
              //   arr.forEach((item) => {
              //     item.addPoint([x, Math.round(Math.random() * 200)], false, shift, { duration: 1000 })
              //   })
              //
              //   chart.redraw()
              // }, 3000)
            }
          },
          zoomType: 'x'
        },

        time: {
          useUTC: false
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
            type: 'day',
            count: 1,
            text: '1d'
          }, {
            type: 'all',
            text: 'All'
          }],
          inputEnabled: false,
          selected: 4
        },

        exporting: {
          enabled: false
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
            showInNavigator: true
          }
        },

        series: [
          {
            name: 'running',
            color: '#64a505',
            type: 'area',
            data: [[(new Date()).getTime(), 0]],
            fillColor: {
              linearGradient: {
                x1: 0,
                y1: 0,
                x2: 0,
                y2: 1
              },
              stops: [
                [0, '#64a505'],
                [1, Highcharts.Color(Highcharts.getOptions().colors[0]).setOpacity(0).get('rgba')]
              ]
            }
          },
          {
            name: 'pending',
            color: '#ffc107',
            type: 'area',
            visible: false, // legend for this series by default
            data: [[(new Date()).getTime(), 0]],
            fillColor: {
              linearGradient: {
                x1: 0,
                y1: 0,
                x2: 0,
                y2: 1
              },
              stops: [
                [0, '#ffc107'],
                [1, Highcharts.Color(Highcharts.getOptions().colors[0]).setOpacity(0).get('rgba')]
              ]
            }
          },
          {
            name: 'deferred',
            color: '#f1f128',
            type: 'area',
            visible: false, // legend for this series by default
            data: [[(new Date()).getTime(), 0]],
            fillColor: {
              linearGradient: {
                x1: 0,
                y1: 0,
                x2: 0,
                y2: 1
              },
              stops: [
                [0, '#f1f128'],
                [1, Highcharts.Color(Highcharts.getOptions().colors[0]).setOpacity(0).get('rgba')]
              ]
            }
          },
          {
            name: 'failed',
            color: '#11dea2',
            type: 'area',
            visible: false, // legend for this series by default
            data: [[(new Date()).getTime(), 0]],
            fillColor: {
              linearGradient: {
                x1: 0,
                y1: 0,
                x2: 0,
                y2: 1
              },
              stops: [
                [0, '#11dea2'],
                [1, Highcharts.Color(Highcharts.getOptions().colors[0]).setOpacity(0).get('rgba')]
              ]
            }
          },
          {
            name: 'error',
            color: '#d70f14',
            type: 'area',
            data: [[(new Date()).getTime(), 0]],
            fillColor: {
              linearGradient: {
                x1: 0,
                y1: 0,
                x2: 0,
                y2: 1
              },
              stops: [
                [0, '#d70f14'],
                [1, Highcharts.Color(Highcharts.getOptions().colors[0]).setOpacity(0).get('rgba')]
              ]
            }
          },
          {
            name: 'inactive',
            color: '#8d1407',
            type: 'area',
            data: [[(new Date()).getTime(), 0]],
            fillColor: {
              linearGradient: {
                x1: 0,
                y1: 0,
                x2: 0,
                y2: 1
              },
              stops: [
                [0, '#8d1407'],
                [1, Highcharts.Color(Highcharts.getOptions().colors[0]).setOpacity(0).get('rgba')]
              ]
            }
          },
          {
            name: 'killed',
            color: '#d8c9c7',
            type: 'area',
            data: [[(new Date()).getTime(), 0]],
            fillColor: {
              linearGradient: {
                x1: 0,
                y1: 0,
                x2: 0,
                y2: 1
              },
              stops: [
                [0, '#d8c9c7'],
                [1, Highcharts.Color(Highcharts.getOptions().colors[0]).setOpacity(0).get('rgba')]
              ]
            }
          }
        ]
      }
    }
  }
}
</script>

<style scoped>

</style>
