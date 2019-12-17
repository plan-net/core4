import Vue from 'vue'
import Router from 'vue-router'
import Home from './views/Home.vue'
import BoardsHome from './components/BoardsHome.vue'
import Help from './components/Help.vue'

Vue.use(Router)

export default new Router({
  routes: [
    {
      path: '/',
      component: Home,
      children: [
        {
          name: 'boards-home',
          path: '',
          component: BoardsHome,
          meta: {
            auth: true,
            hideNav: false,
            title: 'Overview'
          }
        },
        {
          name: 'help',
          path: 'help/:widgetId',
          component: Help,
          meta: {
            auth: true,
            hideNav: false,
            title: 'Overview'
          }
        },
        {
          name: 'enter',
          path: 'enter/:widgetId',
          component: Help,
          meta: {
            auth: true,
            hideNav: false,
            title: 'Overview'
          }
        }
      ]
    }
  ]
})
