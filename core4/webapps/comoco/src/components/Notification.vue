<template>
  <v-alert :value="value" :type="type" transition="slide-y-transition">
    {{message}}
    <slot></slot>
  </v-alert>
</template>

<script>
export default {
  name: 'notification',
  props: {
    /**
     * Show/hide notification parameter
     */
    value: {
      type: [Boolean],
      required: false,
      default: false
    },
    /**
     * Type of notifications. Possible types are: success, info, warning and error
     */
    type: {
      type: [String],
      required: false,
      default: 'error'
    },
    /**
     * Notification message
     */
    message: {
      type: [String],
      required: false,
      default: ''
    }
  }
}
</script>

<style scoped>

</style>
