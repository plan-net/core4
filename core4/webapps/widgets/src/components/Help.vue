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
      const data = this.$store.getters.widgetById(this.$route.params.widgetId)
      return data
    },
    path () {
      switch (this.$route.name) {
        case 'help':
          return this.widget.endpoint.help_url
        // case 'widget':
        // case 'enter':
        default:
          return this.widget.endpoint.enter_url
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
  padding: 0 0 0 0;
  iframe {
    width: 100%;
    height: 100%;
  }
}
</style>
