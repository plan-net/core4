<template>
  <v-alert :value="show" :type="type" :transition="transition">
    {{message}}
    <slot></slot>
  </v-alert>
</template>

<script>
export default {
  name: 'notification',
  props: {
    /**
     * Show/hide notification
     */
    show: {
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
    },
    /**
     * Transition type
     */
    transition: {
      type: [String],
      required: false,
      default: 'slide-y-transition'
    }
  }
}
</script>

<style scoped>

</style>
