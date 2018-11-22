export const column = {
  chart: {
    type: 'column',
    backgroundColor: 'transparent'
  },
  title: null,
  colors: ['#fff'],
  series: [{
    dataLabels: {
      enabled: true,
      format: '{y:,.0f}%',
      style: {
        color: '#37474F',
        fontWeight: 600,
        textOutline: '2px contrast'
      },
      x: 2,
      y: 5
    }
  }],
  plotOptions: {
    series: {
      pointWidth: 100,
      dataLabels: {
        enabled: true,
        format: '{y}%',
        style: {
          fontWeight: 'bold',
          color: '#37474F',
          'textOutline': '0px contrast',
          'fontSize': '14px'
        }
      }
    }
  },
  tooltip: {
    enabled: false,
    backgroundColor: '#37474F',
    headerFormat: '',
    pointFormat: '{point.y:,.0f}%',
    style: {
      color: '#fff',
      padding: 0,
      fontWeight: 600
    },
    useHTML: true
  },
  xAxis: {
    categories: ['Male', 'Female'],
    labels: {
      style: {
        color: '#fff',
        fontSize: '16px',
        fontWeight: '400'
      }
    },
    lineWidth: 0,
    minorGridLineWidth: 0,
    lineColor: 'transparent',
    minorTickLength: 0,
    tickLength: 0
  },
  yAxis: {
    lineWidth: 0,
    minorGridLineWidth: 0,
    lineColor: 'transparent',
    minorTickLength: 0,
    tickLength: 0,
    gridLineColor: 'transparent',
    min: 3,
    max: 100,
    labels: {
      enabled: false,
      style: {
        color: '#fff'
      },
      format: '{value}%'
    }
  }
}
export function getChartTemplate (config) {
  const tpl = JSON.parse(JSON.stringify(column))
  return tpl
}
