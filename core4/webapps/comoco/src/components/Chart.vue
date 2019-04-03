<template>
      <vue-highcharts :options="chartOptions" ref="chart"></vue-highcharts>
</template>

<script>

import { Chart } from 'highcharts-vue'
import Highcharts from 'highcharts'
import streamgraph from 'highcharts/modules/streamgraph'

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

// var colors = Highcharts.getOptions().colors
var colors = ['#d70f14', '#8d1407', '#d8c9c7', '#ffc107', '#f1f128', '#11dea2', '#64a505']

export default {
  name: 'JobsStat',
  components: {
    VueHighcharts: Chart
  },
  data () {
    return {
      chartOptions: {
        chart: {
          title: '',
          type: 'streamgraph',
          marginBottom: 30,
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
          },
          plotBorderColor: '#606063'
        },

        // Make sure connected countries have similar colors
        colors: [
          colors[0],
          colors[1],
          colors[2],
          colors[3],
          colors[4],
          // East Germany, West Germany and Germany
          Highcharts.color(colors[5]).brighten(0.2).get(),
          Highcharts.color(colors[5]).brighten(0.1).get(),

          colors[5],
          colors[6],
          colors[7],
          colors[8],
          colors[9],
          colors[0],
          colors[1],
          colors[3],
          // Soviet Union, Russia
          Highcharts.color(colors[2]).brighten(-0.1).get(),
          Highcharts.color(colors[2]).brighten(-0.2).get(),
          Highcharts.color(colors[2]).brighten(-0.3).get()
        ],

        // title: {
        //   floating: true,
        //   align: 'left',
        //   text: 'Winter Olympic Medal Wins'
        // },
        // subtitle: {
        //   floating: true,
        //   align: 'left',
        //   y: 30,
        //   text: 'Source: <a href="https://www.sports-reference.com/olympics/winter/1924/">sports-reference.com</a>'
        // },

        xAxis: {
          top: 10,
          crosshair: true,
          type: 'datetime',
          tickInterval: 1.8e+6, // one week
          // tickInterval: 7 * 24 * 36e5, // one week
          labels: {
            reserveSpace: false,
            format: '{value: %H:%M}',
            // format: '{value:Week %W/%Y}',
            align: 'right',
            rotation: -30
          },
          margin: 10
          // lineWidth: 0,
          // tickWidth: 0
        },
        // xAxis: {
        //   maxPadding: 0,
        //   type: 'category',
        //   crosshair: true,
        //   categories: [],
        //   labels: {
        //     align: 'left',
        //     reserveSpace: false,
        //     rotation: 270,
        //     style: {
        //       color: '#E0E0E3'
        //     }
        //   },
        //   lineWidth: 0,
        //   margin: 10,
        //   tickWidth: 0
        // },

        yAxis: {
          visible: false
          // startOnTick: true,
          // endOnTick: true
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

        plotOptions: {
          series: {
            label: {
              minFontSize: 5,
              maxFontSize: 15,
              style: {
                color: 'rgba(255,255,255,0.75)'
              }
            }
          }
        },

        // annotations: [{
        //   labels: [{
        //     point: {
        //       x: 5.5,
        //       xAxis: 0,
        //       y: 30,
        //       yAxis: 0
        //     },
        //     text: 'Cancelled<br>during<br>World War II'
        //   }, {
        //     point: {
        //       x: 18,
        //       xAxis: 0,
        //       y: 90,
        //       yAxis: 0
        //     },
        //     text: 'Soviet Union fell,<br>Germany united'
        //   }],
        //   labelOptions: {
        //     backgroundColor: 'rgba(255,255,255,0.5)',
        //     borderColor: 'silver'
        //   }
        // }],

        // plotOptions: {
        //   series: {
        //     label: {
        //       minFontSize: 5,
        //       maxFontSize: 15,
        //       style: {
        //         color: 'rgba(255,255,255,0.75)'
        //       }
        //     }
        //   }
        // },
        series: [
          {
            name: 'running',
            color: '#64a505',
            data: [1, 4, 22, 3, 0],
            pointInterval: 1.8e+6,
            pointStart: Date.UTC(2019, 4, 1)
          },
          {
            name: 'error',
            color: '#d70f14',
            data: [7, 14, 7, 9, 1],
            pointInterval: 1.8e+6,
            pointStart: Date.UTC(2019, 4, 1)
          },
          {
            name: 'pending',
            color: '#ffc107',
            data: [3, 0, 0, 1, 18],
            pointInterval: 1.8e+6,
            pointStart: Date.UTC(2019, 4, 1)
          }
        ],
        exporting: {
          sourceWidth: 800,
          sourceHeight: 600
        }
      }
    }
  }
}
</script>

<style scoped>

</style>
