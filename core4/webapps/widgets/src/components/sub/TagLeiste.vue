<template>
  <v-btn-toggle
    v-model="innerSelected"
    tile
    color="primary"
    group
  >
    <v-btn
      :value="item.value"
      text
      v-for="item in tags"
      :key="item.value"
    >
      {{item.label}}
    </v-btn>
  </v-btn-toggle>
</template>

<script>
export default {
  props: {
    selected: {
      type: String,
      required: true,
      default: 'all'
    }
  },

  computed: {
    innerSelected: {
      get () {
        return this.selected
      },
      set (newValue) {
        this.$emit('change', newValue)
      }
    }
  },
  data () {
    return {
      tags: [
        { label: 'All', value: 'all' },
        { label: 'New', value: 'new' },
        { label: 'Tech', value: 'technical' }
      ]
    }
  }

}
</script>

<style lang="scss" scoped>
</style>
