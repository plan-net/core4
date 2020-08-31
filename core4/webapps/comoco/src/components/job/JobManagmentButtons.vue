<template>
  <v-row
    justify="center"
    class="px-3"
  >
    <v-btn
      @click="beforeRestart"
      class="mb-4"
      block
      color="secondary lighten-3"
      :disabled="'running_complete'.includes(job.state) || jobManagerBusy"
      :large="jobCount > 1"
    >Restart</v-btn>
    <v-btn
      @click="beforeKill"
      class="mb-4"
      block
      :disabled="'error_complete_killed'.includes(job.state) || jobManagerBusy"
      color="secondary lighten-3"
      :large="jobCount > 1"
    >Kill</v-btn>
    <v-btn
      @click="beforeRemove"
      block
      color="secondary lighten-3"
      :disabled="'running_complete'.includes(job.state) || jobManagerBusy"
      :large="jobCount > 1"
    >Remove</v-btn>
    <template v-if="jobManagerBusy">
      <v-progress-circular
        indeterminate
        :size="70"
        :width="7"
        color="grey"
      ></v-progress-circular>
    </template>
  </v-row>
</template>

<script>
import { mapState } from 'vuex'
export default {
  props: {
    jobCount: {
      type: Number,
      default: 1,
      required: true
    }
  },
  computed: {
    ...mapState('jobs', [
      'job', 'jobManagerBusy'
    ])
  },
  methods: {
    async beforeKill () {
      if (await this.$root.$confirm.open('„Kill“ selected job?', 'The selected job will be „killed“. Are you sure?', { color: 'primary darken-1', yes: 'Kill' })) {
        this.$store.dispatch('jobs/manageJob', 'kill')
      } else {
        // cancel
      }
    },
    async beforeRestart () {
      if (await this.$root.$confirm.open('Restart selected job?', 'The selected job will be restarted. Are you sure?', { color: 'primary darken-1', yes: 'Restart' })) {
        this.$store.dispatch('jobs/manageJob', 'restart')
      } else {
        // cancel
      }
    },
    async beforeRemove () {
      if (await this.$root.$confirm.open('Remove selected job?', 'The selected job will be removed. Are you sure?', { color: 'primary darken-1', yes: 'Remove' })) {
        this.$store.dispatch('jobs/manageJob', 'delete')
      } else {
        // cancel
      }
    }
  }
}
</script>

<style lang="scss" scoped>
</style>
