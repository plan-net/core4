import Vue from 'vue'
import Router from 'vue-router'
import Home from './views/Home.vue'
import Auth from 'pnbi-base/core4/Auth.js'

Vue.use(Router)

export default new Router({
  routes: [
    {
      path: '/',
      meta: {
        auth: true,
        hideNav: false,
        title: 'Entry'
      },
      name: 'entry',
      component: Home,
      beforeEnter: (to, from, next) => {
        const loggedIn = window.localStorage.getItem('user')
        // TODO: fixme - we should also call profile to see if user is logged in
        if (loggedIn) {
          Auth.profile().then(() => {
            window.location.assign(window.REDIRECTION)
          }, () => {
            window.localStorage.removeItem('user')
          })
        }
        // next()
      }
    }
  ]
})
