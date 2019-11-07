<template>
  <v-row
    no-gutters
    class="border-info"
  >
    <v-col cols="12" style="height: 38px;">
      <v-row no-gutters>

        <!-- Iterate for all states which belongs to the group and display amount of all jobs with this state  -->
        <v-flex
          v-for="(state, index) in states"
          :key="index"
          :class="`state-${state}`"
          class="info-groups"
        >
          <template v-if="state !== 'running'">
            <v-row
              no-gutters
              class="text-truncate pa-1"
            >
              <v-flex xs8>
                <span class="font-weight-bold grey--text">{{ state }}</span>
              </v-flex>
              <v-flex
                class="text-right"
                xs4
              >
                <span class="font-weight-bold grey--text">{{ getStateCounter([state]) }}</span>
              </v-flex>
            </v-row>
          </template>
        </v-flex>
      </v-row>
    </v-col>

    <!-- Display the group name and amount of all jobs which belongs to this group  -->
    <v-col cols="12" class="px-2 pb-2">
      <v-row
        no-gutters
        pa-1
      >
        <v-flex xs9>
          <span class="headline text-lowercase text-truncate">{{ name }}</span>
        </v-flex>
        <v-flex
          class="text-right"
          xs3
        >
          <span class="job-count text-lowercase text-truncate">{{ getStateCounter(states) }}</span>
        </v-flex>
      </v-row>
    </v-col>
  </v-row>
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
@import "../style/comoco";

.border-info {
  height: 76px;
  .headline{
    font-weight: 500;
  }
  .info-groups {
    flex: 1 1 0;

    &:not(:last-child) {
      margin-right: 2px;
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
}
</style>
