import { required, email, max } from 'vee-validate/dist/rules'
import { extend, setInteractionMode } from 'vee-validate'

extend('required', {
  ...required,
  message: 'This field is required'
})

extend('max', {
  ...max,
  message: 'This field must be {length} characters or less'
})

extend('email', {
  ...email,
  message: 'This field must be a valid email'
})

extend('boardexists', {
  validate: (value, { customErrors }) => {
    if (customErrors != null && customErrors.includes('exists')) {
      return false
    }
    return true
  },
  params: ['customErrors'],
  message (val, val2) {
    /*     if (val2.customErrors.includes('core4.error.ArgumentParsingError: parameter [info] expected as_type [dict]')) {
      return `core4.error.ArgumentParsingError: The info yaml should be convertible to valid JSON. The root element should be an object. Example:
        tags:
          - tag1
          - tag2
          - tag3
      `
    }
    if (val2.customErrors.includes('nlc.error.AssetNotFound:')) {
      return 'nlc.error.AssetNotFound: The target of the move operation was not found.'
    } */
    return val2.customErrors
  }
})
setInteractionMode('eager')
