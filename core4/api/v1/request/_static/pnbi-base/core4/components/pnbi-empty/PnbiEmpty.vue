<template>
  <v-alert :value="true" color="warning" icon="warning">
    <span v-if="content.html" class="grey--text" v-html="content.html"></span>
    <span v-else class="grey--text">{{content.label}}</span>
  </v-alert>
</template>

<script>

export default {
  name: 'pnbi-empty',
  props: {
    /**
     * Just a string
     */
    text: {
      type: String | null
    },
    /**
     * Is rendered as html: <strong>No</strong> data
     */
    html: {
      type: String | null
    }
  },
  computed: {
    content () {
      if (this.text) {
        return {
          label: this.text
        }
      }
      if (this.html) {
        return {
          html: this.html
        }
      }
      return this.data
    }
  }
}
</script>

<style lang="css" scoped>
.warning {
  background-color: rgba(0, 0, 0, 0.1) !important;
}
</style>
