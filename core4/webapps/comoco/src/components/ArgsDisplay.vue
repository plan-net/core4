<template>
  <div>
    <pre>{{job.args}}</pre>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
export default {
  props: {
    jobId: {
      type: String,
      default: '',
      required: true
    }
  },
  async mounted () {
    this.$store.dispatch('jobs/fetchJobArgs', this.jobId)
  },
  computed: {
    ...mapGetters('jobs', [
      'job'
    ])
  }
}
</script>

<style lang="scss" scoped>
</style>
