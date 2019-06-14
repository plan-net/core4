<template>
  <v-alert :value="show" :type="type" :transition="transition" :dismissible="dismissible">
    {{message}}
    <slot></slot>
  </v-alert>
</template>

<script>
export default {
  name: 'notification',
  props: {
    method: {
      // @timeout-handler
      type: Function
    },
    /**
     * Show/hide notification.
     */
    show: {
      type: [Boolean],
      required: false,
      default: false
    },
    /**
     * Type of notifications. Possible types are: success, info, warning and error.
     */
    type: {
      type: [String],
      required: false,
      default: 'error'
    },
    /**
     * Notification message.
     */
    message: {
      type: [String],
      required: false,
      default: ''
    },
    /**
     * Sets the component transition.
     * Can be one of the built in transitions or your own.
     * Build in transitions:
     *    - slide-x-transition
     *    - slide-y-transition
     *    - scale-transition
     *    - fade-transition
     *    - expand-transition
     *
     */
    transition: {
      type: [String],
      required: false,
      default: 'slide-y-transition'
    },
    /**
     * Show/hide close icon.
     */
    dismissible: {
      type: [Boolean],
      required: false,
      default: false
    },
    /**
     * Time (in milliseconds) to wait until snackbar is automatically hidden.
     * Use 0 to keep open indefinitely.
     */
    timeout: {
      type: [Number],
      required: false,
      default: 0
    },
    /**
     *  ToDo: add description
     */
    name: {
      type: [String], // socket_reconnect_error
      required: true
    }
  },
  data () {
    return {
      timerId: null
    }
  },
  mounted () {
    this.$nextTick(() => {
      // element has definitely been added to the DOM

      if (this.timeout) {
        this.timerId = setTimeout(() => {
          this.$emit('timeout-handler', this.name, { state: false })
        }, this.timeout)
      }
    })
  },
  beforeDestroy () {
    clearTimeout(this.timerId)
  }
}
</script>

<style scoped>

</style>
