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
import store from '@/store'
// import { config } from '@/main'

export default {
  async beforeRouteEnter (to, from, next) {
    await store.dispatch('widgets/initWidgets')
    next(vm => {})
  },
  mounted: function () {
    /*     this.$bus.$on('c4-application-close', () => {
      this.$router.push('/')
    })
    if (this.widget != null) {
      this.$store.dispatch('setWidgetTitle', this.widget.title)
      this.$store.dispatch('setInWidget', true)

      this.checkAppbarVis()
    } */
  },
  watch: {
    widget (newValue) {
      if (newValue != null) {
        /*         this.$store.dispatch('setWidgetTitle', newValue.title)
        this.$store.dispatch('setInWidget', true) */
      }
    }
  },
  methods: {
    /*     checkAppbarVis () {
      if ((this.widget || {}).spa) {
        this.$store.dispatch('hideAppbar')
      }
    } */
  },
  beforeDestroy () {
    /*     this.$store.dispatch('resetWidgetTitle', config.TITLE)
    this.$store.dispatch('resetInWidget')
    this.$store.dispatch('showAppbar')
    this.$bus.$off('c4-application-close') */
  },
  computed: {
    ...mapGetters(['dark', 'widgetById', 'theme']),
    widget () {
      const data = this.$store.getters['widgets/widgetById'](this.$route.params.widgetId)
      return data
    },
    theme () {
      return JSON.stringify(this.$vuetify.theme.themes)
    },
    path () {
      let path
      switch (this.$route.name) {
        case 'help':
          path = this.widget.endpoint.help_url
          break
        default:
          path = this.widget.endpoint.enter_url
      }
      const dark = new URLSearchParams(this.$vuetify.theme.themes.dark).toString().split('&').join('xyz')
      const light = new URLSearchParams(this.$vuetify.theme.themes.light).toString().split('&').join('xyz')
      const search = this.$route.params.payload
      return `${path}&dark=${this.dark}&themeDark=${dark}&themeLight=${light}&search=${search}`
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
