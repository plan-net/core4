var fs = require('fs')

fs.readFile('../../__init__.py', 'utf8', function (err, data) {
  if (err) throw err
  data = data.split("'").join('"')

  const s1 = data.substring(data.indexOf('name = ') + 7)
  const name = s1.substring(0, s1.indexOf('title')).split('"').join('').replace('\n', '')

  const s3 = data.substring(data.indexOf('__version__ =') + 14)
  const version = s3.substring(0, s3.indexOf('__built__')).split('"').join('').replace('\n', '')
  const all = name + '-' + version

  fs.readFile('./dist/index.html', 'utf8', function (err, data) {
    if (err) throw err
    const tmp = data.split('</head>')
    const version = '<script>window.__VERSION__ ="' + all + '"</script></head>'
    const res = tmp[0] + version + tmp[1]

    fs.writeFile('./dist/index.html', res, function (err) {
      if (err) {
        return console.log(err)
      }
    })
  })
})
