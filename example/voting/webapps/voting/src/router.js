import Vue from 'vue'
import Router from 'vue-router'
import Voting from './views/Voting.vue'
import Admin from './views/Admin.vue'

Vue.use(Router)

export default new Router({
  routes: [
    {
      path: '/',
      name: 'admin',
      component: Admin,
      meta: {
        auth: false,
        title: 'Admin'
      }
    },
    {
      path: '/voting',
      name: 'voting',
      component: Voting,
      meta: {
        auth: false,
        title: 'TODO'
      }
    },
    {
      path: '/question/:sid?',
      name: 'questions',
      meta: {
        auth: false,
        title: 'Fragen'
      },
      // route level code-splitting
      // this generates a separate chunk (about.[hash].js) for this route
      // which is lazy-loaded when the route is visited.
      component: () => import(/* webpackChunkName: "about" */ './views/Question.vue')
    },
    {
      path: '/result/:sid?',
      name: 'result',
      meta: {
        auth: false,
        title: 'Ergebnis'
      },
      // route level code-splitting
      // this generates a separate chunk (about.[hash].js) for this route
      // which is lazy-loaded when the route is visited.
      component: () => import(/* webpackChunkName: "about" */ './views/Result.vue')
    }
  ]
})
