import { jobColors } from '../../settings'
import Highcharts from 'highcharts'

function series () {
  const arr = []

  for (const key in jobColors) {
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

const options = {
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
      // ToDo: implement call queue history when zoom
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

  series: series(),
  credits: {
    text: ''
  }
}

export default {
  ...options
}
