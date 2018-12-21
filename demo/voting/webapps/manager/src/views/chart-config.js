export const column = {
  chart: {
    type: 'column',
    backgroundColor: 'transparent',
    borderWidth: 0,
    plotBorderWidth: 0,
    marginTop: 60,
    width: 1000
    /*     paddingTop: 120,
    marginTop: 40 */
  },
  title: {
    text: 'Example with bold text',
    xxxalign: 'left',
    /*     x: 0,
    y: -5, */
    style: { 'color': '#fff', 'fontSize': '18px' }
  },
  colors: ['#fff'],
  series: [{
    dataLabels: {
      enabled: true,
      format: '{y:,.1f}%',
      style: {
        color: 'red',
        fontWeight: 600,
        textOutline: '2px contrast'
      },
      x: 20,
      y: 5
    }
  }],
  plotOptions: {
    series: {
      pointWidth: 100,
      dataLabels: {
        enabled: true,
        format: '{y:,.1f}%',
        crop: false,
        overflow: 'none',
        style: {
          fontWeight: 'bold',
          color: '#fff',
          'textOutline': '0px contrast',
          'fontSize': '14px'
        }
      }
    }
  },
  tooltip: {
    enabled: true,
    backgroundColor: '#37474F',
    headerFormat: '',
    pointFormat: '{point.y:,.1f}%',
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
        fontSize: '15px',
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
    lineColor: '#4b616e',
    minorTickLength: 0,
    tickLength: 0,
    gridLineColor: '#4b616e',
    min: 3,
    max: 100,
    labels: {
      enabled: true,
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
