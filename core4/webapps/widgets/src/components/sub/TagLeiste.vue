<template>
  <div style="min-width: 120px;">
    <v-btn-toggle
      v-model="innerSelected"
      xxtile
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
  </div>
</template>

<script>
import { mapState } from 'vuex'
export default {
  props: {
    selected: {
      type: String,
      required: true,
      default: 'all'
    }
  },
  components: {

  },
  computed: {
    innerSelected: {
      get () {
        return this.selected
      },
      set (newValue) {
        if (newValue !== this.selected) {
          this.$emit('change', newValue)
        }
      }
    },
    ...mapState('widgets', [
      'tags'
    ])

  },
  data () {
    return {
    }
  }

}
</script>

<style lang="scss" scoped>
</style>
