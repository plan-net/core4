<template>
  <v-text-field
    v-model="text"
    ref="searchRef"
    class="search mr-2"
    hide-details
    clearable
    outlined
    label="Search"
    prepend-inner-icon="mdi-feature-search"
    append-icon="mdi-send"
    v-on:keyup.enter="submit"
    v-on:keyup.esc="esc"
    @click:append="submit"
    @click:clear="clear"
  >
  </v-text-field>
</template>

<script>
export default {
  name: 'search',
  props: {
    searchActive: {
      type: Boolean
    }
  },

  data () {
    return {
      text: ''
    }
  },
  created () {
    this.$nextTick(function () {
      this.$refs.searchRef.focus()
    })
  },
  methods: {
    submit () {
      this.$emit('close-input', { type: (this.text.length) ? 'submit' : 'clear', text: this.text })
    },
    clear () {
      this.$emit('close-input', { type: 'clear' })
    },
    esc () {
      this.$emit('close-input', { type: 'esc' })
    }
  }
}
</script>

<style lang="scss" scoped>

.v-input__icon--append{

}
</style>
