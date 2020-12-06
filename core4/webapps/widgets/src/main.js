import Vue from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'

import Core4ui from 'core4ui/core4'
import '@/vee.js'
import InfiniteLoading from 'vue-infinite-loading'

import VueFriendlyIframe from 'vue-friendly-iframe'
Vue.use(InfiniteLoading, {
  props: {
    spinner: 'bubbles'
    /* other props need to configure */
  },
  system: {
    throttleLimit: 25
    /* other settings need to configure */
  },
  slots: {
    noMore: 'No more search results …', // you can pass a string value
    noResults: 'No results …'
  }
})

Vue.use(VueFriendlyIframe)
Vue.use(Core4ui, {
  App,
  router,
  store,
  config: {
    TITLE: 'Core4os'
  }
})
