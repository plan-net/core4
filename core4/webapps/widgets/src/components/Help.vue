<template>
  <div>
    <iframe
      v-if="widget"
      :src="path"
      frameborder="0"
    ></iframe>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import { config } from '@/main'

export default {
  mounted: function () {
    this.$bus.$on('c4-application-close', () => {
      this.$router.push('/')
    })
    if (this.widget != null) {
      this.$store.dispatch('setWidgetTitle', this.widget.title)
      this.$store.dispatch('setInWidget', true)

      this.checkAppbarVis()
    }
  },
  watch: {
    widget (newValue) {
      if (newValue != null) {
        this.$store.dispatch('setWidgetTitle', newValue.title)
        this.$store.dispatch('setInWidget', true)
      }
    },
    qualName (newValue) {
      this.checkAppbarVis()
    }
  },
  methods: {
    checkAppbarVis () {
      if (this.isWidgetSpa) {
        this.$store.dispatch('hideAppbar')
      }
    }
  },
  beforeDestroy () {
    this.$store.dispatch('resetWidgetTitle', config.TITLE)
    this.$store.dispatch('resetInWidget')
    this.$store.dispatch('showAppbar')
    this.$bus.$off('c4-application-close')
  },
  computed: {
    ...mapGetters(['dark']),
    isWidgetSpa () {
      console.log(this, '########')
      return this.qualName.includes('CoreStaticFileHandler')
    },
    qualName () {
      return (this.widget || {}).qual_name
    },
    widget () {
      const data = this.$store.getters.widgetById(this.$route.params.widgetId)
      return data
    },

    path () {
      /*       if ((this.widget || {}).qual_name.includes('JobHistoryHandler') ||
      (this.widget || {}).title === 'about core4os') { */
      let path
      switch (this.$route.name) {
        case 'help':
          path = this.widget.endpoint.help_url
          break
        default:
          path = this.widget.endpoint.enter_url
      }
      return `${path}&dark=${this.dark}`
      /*       }
      return 'http://localhost:8085/#/' */
    }
  }

}
</script>

<style scoped lang="scss">
div {
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
