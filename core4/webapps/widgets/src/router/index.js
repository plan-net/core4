import Vue from 'vue'
import VueRouter from 'vue-router'
import store from '@/store'
// import Home from '../views/Home.vue'
// import Help from '../views/Help.vue'

Vue.use(VueRouter)

const routes = [
  {
    name: 'enter',
    path: '/enter/:widgetId/:endpoint/:payload?',
    component: () =>
      import(/* webpackChunkName: "help" */ '../views/Help.vue')
  },
  {
    name: 'help',
    path: '/help/:widgetId/:endpoint',
    component: () =>
      import(/* webpackChunkName: "help" */ '../views/Help.vue')
  },
  {
    path: '/:board?',
    name: 'Home',
    component: () =>
      import(/* webpackChunkName: "home" */ '../views/Home.vue')
  }
]

const router = new VueRouter({
  routes
})
const fetchBoards = ['content', 'help', 'notfound', 'enter']
router.beforeEach((to, from, next) => {
  console.log(to.name, 'router.beforeEach')
  if (fetchBoards.includes(to.name)) {
    store.dispatch('widgets/fetchBoards', { type: 'light' })
  }
  next()
})

export default router
