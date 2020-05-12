const theme = {
  colors: [
    '#2b908f',
    '#90ee7e',
    '#f45b5b',
    '#7798BF',
    '#aaeeee',
    '#ff0066',
    '#eeaaee',
    '#55BF3B',
    '#DF5353',
    '#7798BF',
    '#aaeeee'
  ],
  chart: {
    backgroundColor: '#fff',
    // backgroundColor: {
    //   linearGradient: { x1: 0, y1: 0, x2: 1, y2: 1 },
    //   stops: [
    //     [0, '#393939'],
    //     [1, '#3e3e40']
    //   ]
    // },
    style: {
      fontFamily: '\'Unica One\', sans-serif'
    },
    plotBorderColor: '#d6d6dc'
  },

  title: {
    style: {
      color: '#c4c4c9',
      textTransform: 'uppercase',
      fontSize: '20px'
    }
  },

  subtitle: {
    style: {
      color: '#c4c4c9',
      textTransform: 'uppercase'
    }
  },

  xAxis: {
    gridLineColor: '#73080d',
    labels: {
      style: {
        color: '#98989c'
      }
    },

    // lineColor: '#707073',
    // minorGridLineColor: '#505053',
    // tickColor: '#707073',
    title: {
      style: {
        color: '#A0A0A3'

      }
    }
  },

  yAxis: {
    gridLineColor: '#c4c4c9',
    labels: {
      style: {
        color: '#98989c'
      }
    },
    lineColor: '#d6d6dc',
    minorGridLineColor: '#c4c4c9',
    tickColor: '#707073',
    tickWidth: 1,
    title: {
      style: {
        color: '#A0A0A3'
      }
    }
  },

  tooltip: {
    backgroundColor: '#ffffff',
    style: {
      color: '#727275'
    }
  },

  plotOptions: {
    series: {
      dataLabels: {
        color: '#FFFFFF'
        // color: '#B0B0B3'
      },
      marker: {
        lineColor: '#FFFFFF'
      }
    },
    boxplot: {
      fillColor: '#FFFFFF'
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
      color: '#89898c'
    },
    itemHoverStyle: {
      color: '#454547'
    },
    itemHiddenStyle: {
      color: '#f2f2f2'
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

  scrollbar: {
    barBackgroundColor: '#C0C0C8',
    barBorderColor: '#808083',
    buttonArrowColor: '#454547',
    buttonBackgroundColor: '#e7e7ee',
    buttonBorderColor: '#C0C0C8',
    rifleColor: '#FFF',
    trackBackgroundColor: '#fafaff',
    trackBorderColor: '#C0C0C8'
  },

  // Highstock specific
  navigator: {
    xAxis: {
      gridLineColor: '#D0D0D8'
    }
  },
  rangeSelector: {
    buttonTheme: {
      fill: 'white',
      stroke: '#C0C0C8',
      'stroke-width': 1,
      states: {
        select: {
          fill: '#D0D0D8'
        }
      }
    }
  },

  // special colors for some of the
  legendBackgroundColor: 'rgba(0, 0, 0, 0.5)',
  background2: '#505053',
  dataLabelsColor: '#B0B0B3',
  textColor: '#C0C0C0',
  contrastTextColor: '#F0F0F3',
  maskColor: 'rgba(255,255,255,0.3)'
}

export default {
  ...theme
}
