import PnbiWebapp from './components/pnbi-webapp/PnbiWebapp'
import PnbiPage from './components/pnbi-page/PnbiPage'
import PnbiCard from './components/pnbi-card/PnbiCard'
import PnbiDialog from './components/pnbi-dialog/PnbiDialog'
import PnbiNumbers from './components/pnbi-numbers/PnbiNumbers'
import { setRoutes } from './internal/routes/index.js'
import { setAjaxConfig } from './internal/axios.config.js'
import { setCookieConfig } from './internal/cookie.service.js'
import { setStore } from './store'
import PnbiDataTable from './components/pnbi-table/PnbiTable'
// import PnbiDataTablePlus from './components/pnbi-table-plus/PnbiTablePlus'
import PnbiEmpty from './components/pnbi-empty/PnbiEmpty'
import bus from './event-bus'
import helper from './helper'
import './plugins/vee-validate'
import VeeValidate, { Validator } from 'vee-validate'
import en from 'vee-validate/dist/locale/en'
import Router from 'vue-router'
// Vee-Validator
// app wide styles, fonts

import Vuetify from 'vuetify'
import 'material-design-icons-iconfont/dist/material-design-icons.css'

import 'vuetify/dist/vuetify.min.css'
import './styles/typography.scss'
import './styles/index.scss'
import './styles/theme-dark.scss'
import './styles/theme-light.scss'

import numbro from 'numbro'
import deDE from 'numbro/languages/de-DE.js'

import { i18n, veeValidateDictionary } from './translations'

numbro.registerLanguage(deDE)
numbro.setLanguage(deDE.languageTag)

const install = (Vue, options) => {
  Vue.prototype.i18n = i18n
  Vue.prototype.$bus = bus
  Vue.prototype.$helper = helper
  Vue.prototype.$store = options.store
  Vue.prototype.$numbro = numbro
  /// /////////////////

  Vue.use(Router)
  Vue.use(VeeValidate, {
    aria: false,
    locale: 'en'
  })
  Validator.localize('en', en)
  Validator.localize(veeValidateDictionary)
  // 1. setup store (holds all informations)
  setStore(options.store)
  options.store.dispatch('initializeApp', options.config)
  // 2.
  setRoutes(options.router)
  // 3
  setAjaxConfig(options.config)
  setCookieConfig(options.config.API)

  Vue.component('pnbi-dialog', PnbiDialog)
  Vue.component('pnbi-numbers', PnbiNumbers)
  Vue.component('pnbi-card', PnbiCard)
  Vue.component('pnbi-page', PnbiPage)
  Vue.component('pnbi-datatable', PnbiDataTable)
  Vue.component('pnbi-webapp', PnbiWebapp)
  Vue.component('pnbi-empty', PnbiEmpty)

  Vue.use(Vuetify, {
    theme: options.config.THEME,
    iconfont: 'md',
    options: {
      customProperties: true, // color: var(--v-primary-base)
      themeVariations: ['primary', 'accent', 'secondary', 'warning']
    }
  })
}

export default {
  install
}

export { PnbiWebapp }
