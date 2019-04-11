import Vue from 'vue'
import Router from 'vue-router'
import WebComponentsWrapper from './WebComponentWrapper.vue'
import Forgot from '../../internal/routes/auth/Forgot.vue'
import Reset from '../../internal/routes/auth/Reset.vue'

Vue.use(Router)

export default new Router({
  routes: [
    {
      path: '*',
      name: 'login',
      component: WebComponentsWrapper,
      beforeEnter: (to, from, next) => {
        const loggedIn = window.localStorage.getItem('user')
        console.log(loggedIn, '--------------------')
        next()
      }
    },
    {
      path: '/reset/',
      component: WebComponentsWrapper,
      // TODO not dry, reuse from default router
      children: [
        {
          path: '',
          component: Forgot
        },
        {
          path: ':token',
          component: Reset,
          beforeEnter: (to, from, next) => {
            // loads password strength dependency, 800kb
            const loader = (a, b, c, d) => {
              a = '//cdnjs.cloudflare.com/ajax/libs/zxcvbn/4.4.2/zxcvbn.js'
              b = document
              c = 'script'
              d = b.createElement(c)
              d.src = a
              d.type = 'text/java' + c
              d.async = true
              a = b.getElementsByTagName(c)[0]
              a.parentNode.insertBefore(d, a)
            }
            loader()
            next()
          }
        }
      ]
    }
  ]
})
