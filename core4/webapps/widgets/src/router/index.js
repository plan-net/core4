import Vue from 'vue'
import VueRouter from 'vue-router'
// import Home from '../views/Home.vue'
// import Help from '../views/Help.vue'

Vue.use(VueRouter)

const routes = [
  {
    name: 'enter',
    path: '/enter/:widgetId/:payload?',
    component: () =>
      import(/* webpackChunkName: "help" */ '../views/Help.vue')
  },
  {
    path: '/:board?',
    name: 'Home',
    component: () =>
      import(/* webpackChunkName: "home" */ '../views/Home.vue')
  },
  {
    path: '/about',
    name: 'About',
    // route level code-splitting
    // this generates a separate chunk (about.[hash].js) for this route
    // which is lazy-loaded when the route is visited.
    component: () =>
      import(/* webpackChunkName: "about" */ '../views/About.vue')
  }
]

const router = new VueRouter({
  routes
})

export default router
