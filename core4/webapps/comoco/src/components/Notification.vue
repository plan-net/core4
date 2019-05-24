<template>
  <v-alert :value="show" :type="type" :transition="transition" :dismissible="dismissible">
    {{message}}
    <slot></slot>
  </v-alert>
</template>

<script>
import { mapMutations } from 'vuex'

import { ERROR_CHANGE_STATE } from '../store/comoco.mutationTypes'

export default {
  name: 'notification',
  props: {
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
    mutation: {
      type: [String],
      required: true
    }
  },
  data () {
    return {
      timerId: null
    }
  },
  methods: {
    ...mapMutations({
      'showHide': ERROR_CHANGE_STATE
    })
  },
  mounted () {
    this.$nextTick(() => {
      // element has definitely been added to the DOM

      if (this.timeout) {
        this.timerId = setTimeout(() => {
          this.showHide({ errType: this.mutation, stateValue: false })
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
