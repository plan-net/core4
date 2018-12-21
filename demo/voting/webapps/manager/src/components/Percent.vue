<template>
  <div>
<!--       <h4 v-if="(question || {}).state === 'OPEN'" class="display-4 grey--text text-xs-center">{{percent}}%</h4> -->
      <v-progress-circular dark
      :rotate="-90"
      :size="400"
      :width="50"
      :value="percent"
      color="accent"
    >
      {{ percent }}%
    </v-progress-circular>
  </div>
</template>
<script>
import {
  mapGetters,
  mapActions
} from 'vuex'
export default {
  components: {},
  created () {},
  methods: {
    ...mapActions([])
  },
  mounted () {},

  data () {
    return {}
  },
  watch: {},
  computed: {
    ...mapGetters(['question', 'peopleCount']),
    percent () {
      try {
        const p = this.question.n / this.peopleCount
        if (isNaN(p)) {
          throw new Error('No Number')
        }
        return (p * 100).toFixed(1)
      } catch (err) {}
      return 0
    }
  }
}

</script>
<style lang="css" scoped>
  div >>> .v-progress-circular__info{
    font-size: 100px;
    letter-spacing: -0.5rem
  }
</style>
