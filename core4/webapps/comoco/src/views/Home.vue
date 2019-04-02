<template>
  <pnbi-page>
    <v-layout column>
      <v-flex>
        <v-layout row wrap xs12>
          <v-flex v-for="(states, group) in groupsJobsByStates" :key="group" class="ma-2 flex-equal-size">
            <board xs12 md4 lg4 xl4 :name="group" :flags="flags" :states="states"></board>
          </v-flex>
        </v-layout>
      </v-flex>
<!--      <v-flex ma-2 hidden-sm-and-down>-->
<!--        <chart></chart>-->
<!--      </v-flex>-->
    </v-layout>
  </pnbi-page>
</template>

<script>
import { groupsJobsByStates, jobFlags } from '../settings'

import Board from '@/components/Board'
// import Chart from '@/components/Chart'

export default {
  name: 'home',
  components: {
    Board
  },
  data () {
    return {
      groupsJobsByStates: groupsJobsByStates, // {waiting: [pending, ..., failed], running: [running], stopped: [error, ..., killed]
      flags: jobFlags // Z R N K
    }
  }
}
</script>

<style scoped lang="scss">
.flex-equal-size {
  flex: 1 1 0;
}
</style>
