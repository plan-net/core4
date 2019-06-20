import VueI18n from 'vue-i18n'
import Vue from 'vue'

Vue.use(VueI18n)

const i18n = new VueI18n({
  locale: 'en',
  fallbackLocale: 'en',
  messages: {
    en: {
      'waiting': 'olha',
      // 'waiting': 'waiting',
      'running': 'running',
      'stopped': 'stopped'
    },
    de: {
      'waiting': 'warten',
      'running': 'laufen',
      'stopped': 'gestoppt'
    }
  }
})

export { i18n }
