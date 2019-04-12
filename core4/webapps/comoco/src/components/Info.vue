<template>
  <v-layout column xs12 class="border-info">
    <v-flex xs12>
      <v-layout row xs12>

        <!-- Iterate for all states which belongs to the group and display amount of all jobs with this state  -->
        <v-flex v-for="(state, index) in states" :key="index" :class="`state-${state}`" class="info-groups">
          <v-layout row xs12 class="text-truncate pa-1">
            <v-flex xs8>
              <span class="font-weight-bold grey--text">{{ state }}:</span>
            </v-flex>
            <v-flex class="text-right" xs4>
              <span class="font-weight-bold grey--text">{{ getStateCounter([state]) }}</span>
            </v-flex>
          </v-layout>
        </v-flex>
      </v-layout>
    </v-flex>

    <!-- Display the group name and amount of all jobs which belongs to this group  -->
    <v-flex xs12>
      <v-layout row xs12 pa-1>
        <v-flex xs9>
          <span class="font-weight-bold headline text-lowercase text-truncate">{{ name }}</span>
        </v-flex>
        <v-flex class="text-right" xs3>
          <span class="font-weight-bold headline text-lowercase text-truncate">{{ getStateCounter(states) }}</span>
        </v-flex>
      </v-layout>
    </v-flex>
  </v-layout>
</template>

<script>
import { mapGetters } from 'vuex'

export default {
  name: 'board-header',
  props: {
    /**
     * Jobs group name
     */
    name: {
      type: [String],
      required: true
    },
    /**
     * All job states which belongs to the group, use in loop
     */
    states: {
      type: [Array],
      required: true
    }
  },
  computed: {
    ...mapGetters(['getStateCounter'])
  }
}
</script>

<style scoped lang="scss">
@import '../style/comoco';

.border-info{
  background-color:  #282828;

  .info-groups{
    flex: 1 1 0;

    &:not(:last-child){
      margin-right: 2px;
    }
  }
}

.state-pending {
  border-top: 5px solid $pending;
}

.state-deferred {
  border-top: 5px solid $deferred;
}

.state-failed {
  border-top: 5px solid $failed;
}

.state-running {
  border-top: 5px solid $running;
}

.state-error {
  border-top: 5px solid $error;
}

.state-inactive {
  border-top: 5px solid $inactive;
}

.state-killed {
  border-top: 5px solid $killed;
}
</style>
