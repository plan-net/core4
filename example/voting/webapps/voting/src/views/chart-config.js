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
      dataLabels: {
        enabled: true,
        format: '{y}%',
        style: {
          fontWeight: 'bold',
          color: '#7da1b9',
          'textOutline': '0px contrast',
          'fontSize': '14px'
        }
      }
    }
  },
  tooltip: {
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
        fontSize: '12px',
        fontWeight: '400'
      }
    }
  },
  yAxis: {
    lineColor: '#ddd',
    lineWidth: 1,
    min: 3,
    max: 100,
    labels: {
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
