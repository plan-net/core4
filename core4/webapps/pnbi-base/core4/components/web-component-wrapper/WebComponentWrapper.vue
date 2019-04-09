<template>
    <div
      class="auth-wrapper" >
      <component v-bind:is="currentAuthComponent"></component>
    </div>
</template>

<script>
import Login from '../../internal/routes/auth/Login.vue'
import ResetWrapper from '../../internal/routes/auth/AuthWrap.vue'

import router from './router'
import Vue from 'vue'

import Vuex from 'vuex'
import { setStore } from '../../store'

import VeeValidate, { Validator } from 'vee-validate'
import { i18n, veeValidateDictionary } from '../../translations'
import en from 'vee-validate/dist/locale/en'

import 'vuetify/dist/vuetify.min.css'
import Vuetify from 'vuetify'

import 'material-design-icons-iconfont/dist/material-design-icons.css'

import THEME from '../../themes/pnbi/theme-vuetify'
import '../../themes/pnbi/theme-pnbi.scss'
import '../../styles/typography.scss'
import '../../styles/index.scss'
import '../../styles/theme-dark.scss'
import '../../styles/theme-light.scss'

Vue.prototype.i18n = i18n

Vue.use(VeeValidate, {
  aria: false,
  locale: 'en'
})
Validator.localize('en', en)
Validator.localize(veeValidateDictionary)
Vue.use(Vuetify, {
  theme: THEME,
  iconfont: 'md',
  options: {
    customProperties: true,
    themeVariations: ['primary', 'accent', 'secondary', 'warning']
  }
})
Vue.use(Vuex)
const store = new Vuex.Store({})
setStore(store)
export default {
  i18n,
  router,
  store,
  name: 'auth-wrapper',
  components: {
    Login,
    ResetWrapper
  },
  computed: {
    currentAuthComponent () {
      if (this.$route.name === 'login') {
        return 'login'
      }
      return 'reset-wrapper'
    }
  }
}
</script>
