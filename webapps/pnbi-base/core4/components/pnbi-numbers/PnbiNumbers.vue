<template>
    <v-text-field :disabled="disabled" :label="label" autocomplete="off" v-model="internalValue" @keydown.native.stop="onKeyDown" :error-messages="errorMessages" :error="errorMessages.length > 0"
      :suffix="suffix"></v-text-field>
</template>

<script>
import is from 'is'
export default {
  name: 'pnbi-numbers',

  $_veeValidate: {
    // fetch the current value from the innerValue defined in the component data.
    // neeeded for vee-validate error passing and display inside pnbi-numbers
    value () {
      return this.value
    },
    name () {
      return this.label
    }
  },
  props: {
    /**
     * v-model
    */
    value: {
      type: Number,
      default: null
    },
    /**
     * See v-text-field docs
    */
    label: {
      type: String,
      default: null,
      required: false
    },
    /**
     * See v-text-field docs
    */
    disabled: {
      type: Boolean,
      default: false
    },
    /**
     * Displayed after v-text-field.
     * See v-text-field docs
    */
    suffix: {
      type: String,
      required: false,
      default: '€'
    },
    /**
     * Parent component errorMessages object containing errors for this instance
    */
    errorMessages: {
      type: Array,
      default: () => [],
      required: false
    },
    /**
     * Value by which the v-model is multiplied.<br>
     * Example: unit=1000, v-model=1000000; displayed value: <strong>1.000</strong>
     * Suffix should be set to <strong>>T€</strong> (ThousandsEuro) if unit=1000
    */
    unit: {
      type: Number,
      required: false,
      default: 1
    }
  },
  // mounted () {
  /*     console.warn('TODO: check pnbi-numbers implementation. Remove error, remove type, use suffix for type')
    this.$nextTick(function () {
      this.$validator.validateAll()
    }) */
  // },
  methods: {
    /** Triggered onKeyDown in component.
    * Supported keyboard keys (only digits): 1234567890, down,up,left,right arrow
    * On up/down click v-model is incremented, decremented
    * @event keydown
    * @type {Event}
    */
    onKeyDown (event) {
      if (event.keyCode === 38) { // up
        this.internalValue = (this.value / this.unit) + this.incrementor
        return false
      }
      if (event.keyCode === 40) { //  down
        this.internalValue = Math.max((this.value / this.unit) - this.incrementor, 0)

        return false
      }
      if (
        (event.keyCode >= 48 && event.keyCode <= 57) ||
          (event.keyCode >= 96 && event.keyCode <= 105) ||
          event.keyCode === 8 ||
          event.keyCode === 9 ||
          event.keyCode === 37 ||
          event.keyCode === 39 ||
          event.keyCode === 46 ||
          event.keyCode === 110 ||
          event.keyCode === 188 ||
          event.keyCode === 35 ||
          event.keyCode === 36
      ) {} else {
        event.preventDefault()
      }
    }
  },
  computed: {
    internalValue: {
      get: function () {
        if (is.number(this.value)) {
          return (this.value / this.unit).toLocaleString('de-DE')
        }
      },
      set: function (newValue) {
        if (newValue === '') {
          this.$emit('input', null)
          return
        }
        if (is.number(newValue)) {
          this.$emit('input', newValue * this.unit)
        } else {
          this.$emit('input', Number(newValue.replace(/\./g, '').replace(/,/g, '.')) * this.unit)
        }
      }
    },
    incrementor () {
      return (this.unit === 1) ? 1000 : 1
    }
  }
}
</script>

<style scoped>
</style>
