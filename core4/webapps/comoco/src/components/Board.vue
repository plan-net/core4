<template>
  <v-container
    class="board"
    :class="{'full-size': !stockChartVisible}"
  >

    <!-- Group info (counter all of jobs with the same states) -->
    <info
      :name="name"
      :states="states"
    ></info>
    <transition-group
      name="jobs-list"
      tag="v-row"
      class="nowrap jobs mt-3"
    >
      <!-- list of all jobs which belongs to this group -->
      <v-col
        cols="12"
        v-for="job in getJobsByGroupName(name)"
        :key="job.key"
        class="jobs-list-item pt-0 pb-1 px-3"
      >
        <job
          :flags="flags"
          :job="job"
        ></job>
      </v-col>
    </transition-group>
  </v-container>
</template>

<script>
import { mapGetters } from 'vuex'

import Job from '@/components/Job'
import Info from '@/components/Info'

export default {
  name: 'board',
  components: {
    Job, Info
  },
  props: {
    /**
     * Jobs group name
     */
    name: {
      type: [String],
      required: true,
      default: 'Other'
    },
    /**
     * Possible flags for job, needed for "Job" component
     */
    flags: {
      type: [Object],
      required: false
    },
    /**
     * All job states which belongs to this group, need for "Info" component
     */
    states: {
      type: [Array],
      required: true
    }
  },
  computed: {
    ...mapGetters(['getJobsByGroupName']),
    ...mapGetters('app', [
      'stockChartVisible'
    ])
  },
  mounted () {}
}
</script>

<style scoped lang="scss">
@import "../style/comoco";
@import "../style/theme-dark";
@import "../style/theme-light";

.jobs-list-item {
  transition: all 0.5s;
}

.jobs-list-enter {
  opacity: 0;
  transform: translateY(15px);
}

.jobs-list-enter-active {
}

.jobs-list-leave {
  opacity: 0;
  transform: translateY(15px);
}

.jobs-list-leave-active {
  transform: translateY(15px);
}

.jobs-list-leave-to {
  opacity: 0;
  transform: translateY(15px);
}

.board {
  min-width: 230px;
  min-height: 100px;
}

@media (min-width: 960px) {
  .jobs {
    max-height: calc(100vh - 563px);
  }

  .board {
    height: calc(100vh - 450px);
  }
}

@media (min-width: 600px) and (max-width: 960px) {
  .jobs {
    max-height: calc(100vh - 236px);
  }

  .board {
    height: 100%;
  }
}

@media (max-width: 600px) {
  .jobs {
    max-height: calc(100vh - 236px);
  }

  .board {
    height: auto;
  }
}
.container.board.full-size {
  /*   .jobs {
    max-height: 100% !important;
    height: 100% !important;
  }*/
  height: calc(100vh - 85px) !important;
  @media (max-width: 600px) {
    height: auto;
  }
}
</style>
