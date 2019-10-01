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
      this.checkAppbarVis(this.widget.qual_name)
    }
  },
  watch: {
    widget (newValue) {
      if (newValue != null) {
        this.$store.dispatch('setWidgetTitle', newValue.title)
      }
    },
    qualName (newValue) {
      this.checkAppbarVis(newValue)
    }
  },
  methods: {
    checkAppbarVis (val) {
      if ((val || '').includes('CoreStaticFileHandler')) {
        this.$store.dispatch('hideAppbar')
      }
    }
  },
  beforeDestroy () {
    this.$store.dispatch('resetWidgetTitle', config.TITLE)
    this.$store.dispatch('showAppbar')
    this.$bus.$off('c4-application-close')
  },
  computed: {
    ...mapGetters(['dark']),
    qualName () {
      return (this.widget || {}).qual_name
    },
    widget () {
      const data = this.$store.getters.widgetById(this.$route.params.widgetId)
      return data
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
      return `${path}&dark=${this.dark}`
    }
  }

}
</script>

<style scoped lang="scss">
div {
  position: absolute;
  left: 0;
  right: 0;
  top:0;
  bottom: 0;
  background-color: #fff;
  padding: 0 0 0 0;

  iframe {
    width: 100%;
    height: 100%;
  }
}
</style>
