import Vue from 'vue'
import Router from 'vue-router'
import Home from './views/Home.vue'

Vue.use(Router)

export default new Router({
  routes: [
    {
      path: '*',
      meta: {
        auth: true,
        hideNav: false,
        title: 'Entry'
      },
      name: 'entry',
      component: Home,
      beforeEnter: (to, from, next) => {
        const loggedIn = window.localStorage.getItem('user')
        if (loggedIn) {
          window.location.assign(window.REDIRECTION)
        }
        // next()
      }
    }
  ]
})
