import Highcharts from 'highcharts'

Highcharts.dateFormats = {
  W (timestamp) {
    const date = new Date(timestamp)
    const onejan = new Date(date.getFullYear(), 0, 1)
    const week = Math.ceil(
      ((date - onejan) / 86400000 + onejan.getDay() + 1) / 7
    )
    return week
  }
}

/*
Highcharts.setOptions({
})
*/

Highcharts.setOptions({
  global: {
    useUTC: false
  },
  lang: {
    decimalPoint: ',',
    thousandsSep: '.'
  },
  tooltip: {
    yDecimals: 0 // If you want to add 2 decimals
  },
  chart: {
    style: {
      fontFamily: '"Open Sans", serif'
    }
  },
  colors: [
    '#D70F14',
    '#3f515d',
    '#64A505',
    '#DC7300',
    '#C30050',
    '#6c6c6c',
    '#7D0B0E',
    '#05415A',
    '#325005',
    '#A03C00',
    '#640028',
    '#FF3E47',
    '#2CD5E6',
    '#A0CB0E',
    '#FF8500',
    '#F00B69',
    '#969696'
  ],
  credits: {
    enabled: false
  },
  legend: {
    enabled: false
  },
  plotOptions: {
    column: {
      borderWidth: 0,
      colorByPoint: true,
      maxPointWidth: 60
    },
    pie: {
      allowPointSelect: true,
      cursor: 'pointer',
      dataLabels: {
        enabled: false
      },
      showInLegend: true
    }
  },
  title: {
    text: ''
  },
  xAxis: {
    tickColor: 'transparent'
  },
  yAxis: {
    gridLineWidth: 1,
    title: {
      text: '',
      style: {
        color: '#ccc'
      } // Hide
    },
    min: 0
  }
})
