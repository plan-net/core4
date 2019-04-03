<template>
  <div>
    <div class="job mt-1 pa-1" :class="`job-${job.state}`">
      <v-layout column xs12>
        <!-- Job account name -->
        <v-flex class="caption">{{ job.name | accountName }}</v-flex>

        <!-- Job name and amount of jobs with the same name on queue-->
        <v-flex>
          <v-layout row xs12>
            <v-flex xs9 class="text-truncate">
              <span class="font-weight-bold subheading">{{ job.name | shortName }}</span>
            </v-flex>
            <v-flex class="text-right" xs3>
              <span class="font-weight-bold title">{{ job.n }}</span>
            </v-flex>
          </v-layout>
        </v-flex>

        <!-- Existing job flags-->
        <v-flex class="align-right caption">
          <span v-for="(icon, flag) in flags" class="text-uppercase font-weight-bold text--darken-3"
                :key="flag"
                :class="[ (job[flag]) ? 'white--text' : 'grey--text']">
            {{ icon }}
          </span>
        </v-flex>
      </v-layout>
    </div>

    <!-- Job progress bar in %, available only for running jobs -->
<!--    <v-progress-linear v-if="job.state === 'running'"-->
<!--                       color="#64a505"-->
<!--                       height="2"-->
<!--                       :value="job.progress * 100">-->
<!--    </v-progress-linear>-->
  </div>
</template>

<script>
export default {
  name: 'job',
  props: {
    /**
     * Job object
     */
    job: {
      type: [Object],
      required: true
    },
    /**
     * Possible flags for job, needed for "Job" component
     */
    flags: {
      type: [Object],
      required: false
    }
  },
  filters: {
    shortName: value => value.split('.').slice(-1)[0],
    accountName: value => value.split('.')[2]
  }
}
</script>

<style scoped lang="scss">
@import '../style/comoco';

.align-right{
  align-self: flex-end;
}

.v-progress-linear{
  margin: 0;
  top: -2px;
}

.job {
  background-color: $job-panel-bck-color;
  position: relative;

  &:before {
    content: '';
    position: absolute;
    top: 0;
    right: 0;
    width: 0;
    border-top: 10px solid $jobs-board-bck-color;
    border-left: 10px solid $job-panel-bck-color;
  }

  &:hover {
    background-color: #2E2E2E;

    &:before{
      content: '';
      position: absolute;
      top: 0;
      right: 0;
      width: 0;
      border-top: 10px solid $jobs-board-bck-color;
      border-left: 10px solid #2E2E2E;
    }
  }
}

.job-pending {
  border-left: 5px solid $pending;
}

.job-deferred {
  border-left: 5px solid $deferred;
}

.job-failed {
  border-left: 5px solid $failed;
}

.job-running {
  border-left: 5px solid $running;
}

.job-error {
  border-left: 5px solid $error;
}

.job-inactive {
  border-left: 5px solid $inactive;
}

.job-killed {
  border-left: 5px solid $killed;
}
</style>
