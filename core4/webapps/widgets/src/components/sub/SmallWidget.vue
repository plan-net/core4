<template>
  <v-card
    :class="{disabled: oldAdded, 'new-added': newAdded}"
    class="pa-3 mx-4 mb-8"
    height="225"
    width="320"
    @click="onClick"
  >
    <v-card-title class="px-0 pb-0 pt-1">
      <v-row
        align="center"
        justify="start"
        no-gutters
      >
        <v-avatar
          :color="oldAdded ? 'grey':'accent'"
          size="32"
          class="c4-avatar mr-2"
        >
          <v-icon
            style="font-size: 22px;"
            dark
          >{{widget.icon}}</v-icon>
        </v-avatar>
        <v-col>
          <div class="c4-card--widget-title grey--text text--darken-1 body-2">{{widget.title}}</div>
        </v-col>
        <v-chip
          x-small
          v-for="(tag, i) in tags"
          :key="i"
          class="px-1"
          :color="oldAdded ? 'grey':'primary'"
          label
          text-color="white"
        >
          {{tag.toUpperCase()}}
        </v-chip>
      </v-row>
    </v-card-title>
    <v-card-text class="pt-9 px-0">
      <div class="subtitle-2 mb-1´2 text-truncate">{{widget.subtitle}}</div>
      <div class="body-2 font-weight-light">{{widgetDesc}}</div>
      <!--    <pre>{{widget.tag}}</pre> -->
    </v-card-text>

    <v-card-actions class="pa-0">
      <template v-if="addedToCurrentBoard">
        <v-row
          no-gutters
          align="center"
          justify="center"
        >
          <v-col class="pa-0 mb-5 grey--text">{{oldAdded ? 'Added' : 'Removed'}}</v-col>
          <v-checkbox
            class="pa-0 ma-0"
            color="grey"
            :value="oldAdded"
            @click.prevent="()=>{}"
          ></v-checkbox>
        </v-row>
      </template>
      <template v-else>
        <v-spacer></v-spacer>
        <v-checkbox
          class="pa-0 ma-0"
          @click.prevent="()=>{}"
          :value="newAdded"
        ></v-checkbox>
      </template>
    </v-card-actions>

  </v-card>
</template>

<script>
import _ from 'lodash'
// mapActions, mapGetters
import { mapState } from 'vuex'

export default {
  methods: {
    async onClick () {
      if (this.addedToCurrentBoard) {
        this.oldAdded = !this.oldAdded
        await this.$nextTick()
        this.$emit('change', {
          widget: _.cloneDeep(this.widget),
          added: this.oldAdded,
          isNew: false
        })
      } else {
        this.newAdded = !this.newAdded
        this.onNewAddedChange()
      }
    },
    async onNewAddedChange ($event) {
      await this.$nextTick()
      this.$emit('change', {
        widget: _.cloneDeep(this.widget),
        added: this.newAdded,
        isNew: true
      })
    }
  },
  data () {
    return {
      newAdded: false,
      oldAdded: false
    }
  },
  computed: {
    tags () {
      return this.widget.tag.filter(val => {
        return val === 'new'
      })
    },
    ...mapState('widgets', [
      'board', 'widgets'
    ]),
    addedToCurrentBoard: {
      get () {
        const added = this.widgets.find(val => {
          // console.log(val.rsc_id, this.widget.rsc_id)
          return val.rsc_id === this.widget.rsc_id
        })
        return added != null
      },
      set (newValue) {
        console.log('newCheck', newValue)
      }
    },
    widgetDesc () {
      if ((this.widget.description || []).length > 135) {
        return this.widget.description.substring(0, 135) + '…'
      }
      return this.widget.description
    }
  },
  mounted () {
    this.oldAdded = this.addedToCurrentBoard
  },
  props: {
    widget: {
      type: Object,
      required: true,
      default: () => {
        return {
          rsc_id: -1
        }
      }
    }
  }
}
</script>

<style lang="scss" scoped>
::v-deep .v-card__text {
  height: calc(100% - 60px);
}
.v-card {
  border: 2px solid transparent;
  &.disabled {
    background: #f0f0f0;
  }
  &.new-added {
    border: 2px solid var(--v-primary-base);
  }
}
::v-deep .v-chip.v-size--x-small {
  letter-spacing: -0.005rem;
}
.theme--light.v-card > .v-card__text {
  color: rgba(0, 0, 0, 0.87);
}
.c4-card--widget-title {
  width: 99%;
  -webkit-hyphens: auto;
  hyphens: auto;
}
</style>
