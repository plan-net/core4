export function extractError (errMessage) {
  // console.log('errMessage', errMessage)
  if (errMessage == null) {
    return 'No error message found'
  }
  if (typeof errMessage === 'string') {
    if (errMessage.includes('core4.error') || errMessage.includes('tornado.web.HTTPError')) {
      const message1 = errMessage.split(':')
      const message2 = errMessage.split(')')
      const message3 = message2[0].split('(')
      return `${message1[0]}: ${message3[1]}`.replace(/{/g, '')
    }
  }
  return errMessage // 'No error message found'
}

export function formatDate (value) {
  const options = { year: '2-digit', month: 'numeric', day: 'numeric', hour: 'numeric', minute: 'numeric', second: 'numeric' }
  return new Date(value).toLocaleDateString('de-DE', options)
}
