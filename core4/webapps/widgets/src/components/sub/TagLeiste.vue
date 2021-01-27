<template>
  <div style="min-width: 120px;">
    <!--     <pre>
      {{tags}}
    </pre> -->
    <v-combobox
      v-model="innerSelected"
      :items="tags"
      clearable
      outlined
      xxxfilled
      multiple
      small-chips
      item-text="label"
      item-value="value"
      hide-details
      prepend-inner-icon="mdi-tag-plus-outline"
      label="Tags"
    >
      <template v-slot:item="{ attrs, item }">
        <v-checkbox v-model="attrs.inputValue"></v-checkbox>
        {{ item.label }}
        <v-spacer></v-spacer>
        <v-list-item-action @click.stop>
          <v-chip
            color="accent"
            label
            outlined
            small
          >{{item.count}}</v-chip>
        </v-list-item-action>
      </template>
    </v-combobox>
    <!-- <v-btn-toggle
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
    </v-btn-toggle> -->
  </div>
</template>

<script>
import { mapState } from 'vuex'
export default {
  props: {
    selected: {
      type: Array,
      required: true,
      default: () => []
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
