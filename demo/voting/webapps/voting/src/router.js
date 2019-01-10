import Vue from 'vue'
import Router from 'vue-router'
import UserVoting from './views/UserVoting.vue'
Vue.use(Router)

export default new Router({
  routes: [
    {
      path: '/:uid',
      name: 'voting',
      component: UserVoting,
      meta: {
        auth: false,
        title: 'Voting App'
      }
    }
  ]
})
