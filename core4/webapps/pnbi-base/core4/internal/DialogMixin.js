/**
 * @mixin
 */
export default {
  props: {
    /**
     * Sets value/v-model placeholder
     */
    value: {
      required: false
    },
    /**
     * Sets dialog status open or closed from outside
     */
    open: {
      required: false,
      type: Boolean,
      default: false
    }
  },
  computed: {
    /**
     * Handles open/closed state of dialog
     */
    isOpen: {
      get () {
        return this.open
      },
      set () {
        this.$emit('close')
      }
    }
  }
}
