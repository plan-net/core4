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
export default {
  mounted () {
  },
  computed: {
    widget () {
      return this.$store.getters.widgetById(this.$route.params.widgetId)
    },
    path () {
      switch (this.$route.name) {
        case 'help':
          return this.widget.endpoint.help_url
        case 'widget':
          return this.widget.endpoint.enter_url
        default:
          return ''
      }
    }
  }

}
</script>

<style scoped lang="scss">
div {
  position: absolute;
  left: 0;
  right: 0;
  top: 55px;
  bottom: 0;
  background-color: #fff;
  padding: 15px 0 0 15px;
  iframe {
    width: 100%;
    height: 100%;
  }
}
</style>
