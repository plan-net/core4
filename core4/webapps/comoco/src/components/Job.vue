<template>
  <v-row
    @click="onClick"
    no-gutters
    style=""
    class="job px-2 pt-1 pb-0"
    :class="`job-${job.state}`"
  >
    <v-col cols="12">
      <!-- Job account name -->
      <h2 class="caption">{{ job.name | accountName }}</h2>

      <!-- Job name and amount of jobs with the same name on queue-->
      <v-row
        no-gutters
        align="center"
      >
        <v-col class="name text-truncate">
          <v-tooltip bottom>
            <template v-slot:activator="{ on }">
              <span
                v-on="on"
                class="subheading"
              >{{ job.name | shortName }}</span>
            </template>
            <span>{{ job.name }}</span>
          </v-tooltip>
        </v-col>
        <v-col class="text-right">
          <span class="job-count">{{ job.n }}</span>
        </v-col>
      </v-row>
      <job-state :flags="flags" :job="job"/>
    </v-col>
    <!-- Job progress bar in %, available only for running jobs -->
    <v-progress-linear
      v-if="job.state === 'running'"
      color="#64a505"
      height="4"
      :value="job.progress * 100"
    >
    </v-progress-linear>
  </v-row>
</template>

<script>
import JobState from '@/components/job/JobState.vue'
export default {
  components: {
    JobState
  },
  name: 'job',
  props: {
    /**
     * Job object
     */
    job: {
      type: Object,
      required: true
    },
    /**
     * Possible flags for job, needed for "Job" component
     */
    flags: {
      type: Object,
      required: false
    }
  },
  filters: {
    shortName: value => value.split('.').slice(-1)[0],
    accountName: value => value.split('.')[0]
  },
  methods: {
    onClick () {
      this.$store.dispatch('jobs/clearJob')
      this.$store.dispatch('jobs/fetchJobsByName', this.job)
    }
  }
}
</script>

<style scoped lang="scss">
@import "../style/comoco";

.job {
  cursor: pointer;
}
.v-progress-linear {
  margin: 0 -8px 0 -10px;
  width: calc(100% + 20px);
  top: 0;
}
/* .flags {
  margin-top: -2px;
  margin-bottom: 2px;
  font-size: 11.5px;
  padding-right: 3px;
  .flag {
    margin-left: 1px;
  }
} */
.job {
  position: relative;

  &:before {
    content: "";
    position: absolute;
    top: 0;
    right: 0;
    width: 0;

    border-top-width: 10px;
    border-top-style: solid;

    border-left-width: 10px;
    border-left-style: solid;
  }

  /*   &:hover {
    &:before {
      content: "";
      position: absolute;
      top: 0;
      right: 0;
      width: 0;

      border-top-width: 10px;
      border-top-style: solid;

      border-left-width: 10px;
      border-left-style: solid;
    }
  } */

  .name {
    /*     position: relative;
    top: -6px; */
    max-width: 250px;
    .subheading {
      font-weight: 500;
      font-size: 22px;
    }
  }
  .subheading,
  .job-count {
    line-height: 0.8;
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
