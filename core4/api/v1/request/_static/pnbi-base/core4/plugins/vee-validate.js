
// import Auth from './Auth'
// import de from 'vee-validate/dist/locale/de'

/* Validator.extend('caps', {
  validate (value) {
    return /^[A-Z]$/.test(value);
  },
  getMessage (field) {
    return `The ${field}` must only contain capitalized characters`;
  }
}); */

/* const dictionary2 = Validator.dictionary
Validator.extend('auth', {
  validate: value => {
    return projects
      .uniqueProjectName(value, this.$route.params.id)
      .then(unique => {
        if (unique) {
          return {
            valid: true
          }
        }
        return {
          valid: false,
          data: {
            message: 'Der Projektname ist bereits vergeben.'
          }
        }
      })
  },
  getMessage (field, params, data) {
    return dictionary.getFieldMessage(Validator.locale, field, data)
  }
}) */
