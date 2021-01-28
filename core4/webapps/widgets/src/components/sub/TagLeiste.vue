<template>

  <v-row
    no-gutters
    align="center"
  >
    <v-chip
      class="mr-3"
      label
      :color="selected.length === 0 ? 'primary': ''"
      @click="reset"
    >
      All
    </v-chip>
    <v-chip-group
      active-class="primary"
      column
      multiple
      v-model="innerSelected1"
    >
      <v-chip
        label
        v-for="tag in defaultTags"
        :key="tag.value"
      >
        {{ tag.value }}
        <v-avatar
          style="opacity: .5"
          rounded
          v-if="tag.count > 1"
          right
          light
        >
          ({{tag.count}})
        </v-avatar>
      </v-chip>
    </v-chip-group>
    <v-divider
      inset
      vertical
      class="ml-1 mr-3"
      style="margin-top: 8px; margin-bottom: 8px;"
    ></v-divider>
    <v-menu
      max-width="480px"
      offset-y
      :close-on-content-click="false"
    >
      <template v-slot:activator="{ on, attrs }">
        <v-chip
          label
          class="more-chip"
          ripple
          :class="{'primary': innerSelected2Le > 0}"
          v-bind="attrs"
          v-on="on"
        >
          …
        </v-chip>
      </template>
      <v-sheet elevation="5">
        <v-sheet
          class="px-3 pt-3 pb-0 white"
          light
        >
          <v-row
            no-gutters
            align="center"
          >
            <h4>
              Observed Tags
            </h4>
            <v-spacer></v-spacer>
            <v-btn
              class="ml-2"
              icon
            >
              <v-icon>mdi-close</v-icon>
            </v-btn>

          </v-row>
        </v-sheet>

        <div class="pa-4">
          <v-chip-group
            multiple
            active-class="primary"
            v-model="innerSelected2"
          >
            <v-chip
              label
              v-for="tag in observedTags"
              :key="tag.value"
            >
              {{ tag.value }}
              <v-avatar
                style="opacity: .5"
                rounded
                v-if="tag.count > 1"
                right
                light
              >
                ({{tag.count}})
              </v-avatar>
            </v-chip>
          </v-chip-group>
        </div>
      </v-sheet>
    </v-menu>
  </v-row>

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
  methods: {
    reset () {
      this.$emit('change', [])
    }
  },
  computed: {
    innerSelected2Le () {
      return this.innerSelected2.length
    },
    innerSelected2: {
      get () {
        const t = this.observedTags
        console.log(t)
        const t2 = this.selected.filter(val => !val.default).map(val => t.indexOf(val))
        return t2
      },
      set (newValue) {
        const is = this.observedTags
        // index to object // return-object for chip-group not working
        const tmp2 = newValue.map(val => {
          return is[val]
        })
        const tmp = this.selected.filter(val => val.default)
        this.$emit('change', tmp.concat(tmp2))
      }
    },
    innerSelected1: {
      get () {
        const t = this.defaultTags
        const t2 = this.selected.filter(val => val.default).map(val => t.indexOf(val))
        return t2
      },
      set (newValue) {
        const is = this.defaultTags
        const tmp = newValue.map(val => {
          return is[val]
        })
        const tmp2 = this.selected.filter(val => !val.default)
        this.$emit('change', tmp.concat(tmp2))
      }
    },
    ...mapState('widgets', [
      'tags'
    ]),
    defaultTags () {
      return this.tags.filter(val => val.default)
    },
    observedTags () {
      return this.tags.filter(val => !val.default)
    }

  },
  data () {
    return {
    }
  }

}
</script>

<style lang="scss" scoped>
::v-deep .v-divider {
  border-width: 1px !important;
}
::v-deep .more-chip {
  min-width: 60px;
  .v-chip__content {
    margin: -10px auto 0 auto;
    font-size: 20px;
  }
}
</style>
