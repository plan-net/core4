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

const mapping = {
  pending: 0,
  deferred: 1,
  failed: 2,
  running: 3,
  error: 4,
  inactive: 5,
  killed: 6
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
    getChart: {
      handler: function (val, oldVal) {

        if (!this.$refs.chart) {
          return null
        }

        let chart = this.$refs.chart.chart

        for (let key in val) {
          let series = chart.series[mapping[key]]
          let x = (new Date()).getTime()
          let y = Math.round(Math.random() * 100)

          series.addPoint([x, y], false)
        }
        chart.redraw()
      },
      deep: true
    }
  },
  computed: {
    ...mapGetters(['getChart']),
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
        title: {
          floating: true,
          align: 'right',
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
        series: [
          {
            name: 'pending',

            color: '#ffc107',
            data: [[(new Date()).getTime(), 0]]
          },
          {
            name: 'deferred',
            color: '#f1f128',
            data: [[(new Date()).getTime(), 0]]
          },
          {
            name: 'failed',
            color: '#11dea2',
            data: [[(new Date()).getTime(), 0]]
          },
          {
            name: 'running',
            color: '#64a505',
            data: [[(new Date()).getTime(), 0]]
          },
          {
            name: 'error',
            color: '#d70f14',
            data: [[(new Date()).getTime(), 0]]
          },
          {
            name: 'inactive',
            color: '#8d1407',
            data: [[(new Date()).getTime(), 0]]
          },
          {
            name: 'killed',
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
