<template>
  <div class="iframe-container">
    <iframe
      :src="path"
      frameborder="0"
    ></iframe>
    <!-- this little guy displays the title in the core4ui C4-Appbar -->
    <portal to="c4ui-title-portal">

      <h3>
        <v-avatar
          color="accent"
          size="30"
          class="c4-avatar mr-3"
        >
          <v-icon
            small
            dark
          >{{widget.icon}}</v-icon>
        </v-avatar>
        {{widget.title}}
      </h3>
    </portal>
    <!-- this little guy displays the title in the core4ui C4-Appbar -->
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
// import router from '@/router'
import store from '@/store'
// import { config } from '@/main'
import { replacePort } from '@/plugins/fixme.js'

export default {
  async beforeRouteEnter (to, from, next) {
    store.dispatch('widgets/fetchBoards', { type: 'light' })
    next(vm => {})
  },
  async mounted () {
    this.$bus.$on('c4-application-close', () => {
      this.$router.push('/')
    })
    await store.dispatch('widgets/fetchWidget', {
      id: this.$route.params.widgetId,
      endpoint: decodeURIComponent(this.$route.params.endpoint),
      accept: 'application/json'
    })
  },
  watch: {
  },
  methods: {

  },
  beforeDestroy () {
    this.$bus.$off('c4-application-close')
  },
  computed: {
    ...mapGetters(['dark', 'theme']),
    widget () {
      const data = this.$store.getters['widgets/widgetById'](this.$route.params.widgetId)
      return data || {
        icon: ''
      }
    },
    theme () {
      return JSON.stringify(this.$vuetify.theme.themes)
    },
    path () {
      if (this.widget.rsc_id == null) {
        return 'about:blank'
      }
      const user = JSON.parse(window.localStorage.getItem('user') || {})
      const token = `?token=${user.token || -1}`
      const pathEnd = `${this.widget.rsc_id}${token}`
      const ep = decodeURIComponent(this.$route.params.endpoint)
      let path
      switch (this.$route.name) {
        case 'help':
          path = `${ep}/_info/help/${pathEnd}`
          break
        default:
          path = `${ep}/_info/enter/${pathEnd}`
      }
      const dark = new URLSearchParams(this.$vuetify.theme.themes.dark).toString().split('&').join('xyz')
      const light = new URLSearchParams(this.$vuetify.theme.themes.light).toString().split('&').join('xyz')
      const search = this.$route.params.payload || ''
      const ret = `${path}&dark=${this.dark}&themeDark=${dark}&themeLight=${light}&search=${search}`
      return replacePort(ret)
    }
  }

}
</script>

<style scoped lang="scss">
div.iframe-container {
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  background-color: #fff;
  padding: 0 0 0 0;
  iframe {
    width: 100%;
    height: 100%;
  }
}
</style>
