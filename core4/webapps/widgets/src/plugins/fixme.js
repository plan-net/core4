export function replacePort (value) {
  const devPort = window.location.port
  if (devPort.indexOf('80') === 0) {
    return value.replace('5001', '8080')
  }
  return value
}
