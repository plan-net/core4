<template>
  <v-row
    align="center"
    justify="center"
  >
    <template v-if="internalStates.length > 1">
      <span class="text-caption grey--text mr-3">Job state filter</span>
      <v-btn-toggle
        v-model="selected"
        dense
        dark
        multiple
        mandatory
        shaped
        @change="onChange"
      >
        <v-btn
          :color="`${state[1]}`"
          small
          v-for="(state, index) in internalStates"
          :key="state[0]"
        >
          <v-icon v-if="selected.includes(index)">check_box</v-icon>
          <v-icon v-else>check_box_outline_blank</v-icon>
        </v-btn>
      </v-btn-toggle>
    </template>
  </v-row>
</template>

<script>
import { jobColors } from '@/settings'
import { mapGetters } from 'vuex'
export default {
  data () {
    const states = Object.entries(jobColors).map(val => {
      return val
    })
    return {
      states,
      selected: []
    }
  },
  created () {
    this.selected = this.internalStates.map((val, i) => i)
  },
  methods: {
    onChange () {
      const internalS = this.internalStates
      const states = this.selected.map(index => {
        return internalS[index][0]
      })
      this.$store.dispatch('jobs/addStateFilter', states)
    }
  },
  computed: {
    ...mapGetters('jobs', [
      'jobs'
    ]),

    internalStates () {
      const uniqueJobStates = this.jobs.map(val => val.state)
      const dataIn = this.states
      const dataOut = dataIn.filter(val => {
        if (uniqueJobStates.includes(val[0])) {
          return true
        }
        return false
      })
      return dataOut
    }
  }
}
</script>

<style lang="scss" scoped>
</style>
