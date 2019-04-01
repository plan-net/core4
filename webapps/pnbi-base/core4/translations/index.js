import VueI18n from 'vue-i18n'
import Vue from 'vue'

Vue.use(VueI18n)

export const veeValidateDictionary = {
  de: {
    messages: {
      auth: `Bitte überprüfen Sie ihren Namen und das Passwort.`,
      passwordscore: `Das gewählte Passwort ist nicht sicher genug.`,
      confirmspecial: `Die Passwörter stimmen nicht überein.`
    }
  },
  en: {
    messages: {
      auth: `Please check your name and password.`,
      passwordscore: `The chosen password is not secure enough.`,
      confirmspecial: `The passwords do not match.`
    }
  }
}
export const i18n = new VueI18n({
  locale: 'en',
  fallbackLocale: 'en',
  messages: {
    en: {
      'username': 'Username',
      'password': 'Password',
      'backToLogin': 'Back to Login',
      'yourEmailAdress': 'Email Address',
      'checkEmail': 'Please check your email inbox.',
      'resetPassword': 'Reset password',
      'newPassword': 'New password',
      'repeatPassword': 'Repeat password',
      'passwordSecurity': 'Password security',
      'requestNewPassword': 'Request',
      'pw': {
        '0': 'Very weak',
        '1': 'Weak',
        '2': 'Ok',
        '3': 'Good',
        '4': 'Great'
      },
      errors: {
        'is500Error': 'A server error has occurred.<br>Please contact us at:',
        'isAuthError': 'Please log in.',
        'isPermissionsError': 'You are not authorized to access this resource. <br>Please contact us at:'
      }
    },
    de: {
      'username': 'Name',
      'password': 'Passwort',
      'backToLogin': 'Zurück zum Login',
      'yourEmailAdress': 'E-Mail Adresse',
      'checkEmail': 'Bitte überprüfen sie ihren Email-Posteingang.',
      'resetPassword': 'Reset password',
      'newPassword': 'Neues Passwort',
      'repeatPassword': 'Passwort wiederholen',
      'passwordSecurity': 'Passwortsicherheit',
      'requestNewPassword': 'Anfordern',
      'pw': {
        '0': 'Sehr schwach',
        '1': 'Schwach',
        '2': 'Ok',
        '3': 'Gut',
        '4': 'Großartig'
      },
      errors: {
        'is500Error': 'Ein Server Fehler ist aufgetreten.<br>Bitte kontaktieren sie uns unter:',
        'isAuthError': 'Bitte loggen sie sich ein.',
        'isPermissionsError': 'Sie sind nicht authorisiert, diese Ressource aufzurufen.<br>Bitte kontaktieren sie uns unter:'
      }
    }
  }
})
