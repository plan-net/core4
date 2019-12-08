<template>
  <v-container class="board">

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
      <v-col cols="12"
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
    ...mapGetters(['getJobsByGroupName'])
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
  transform: translateX(30px);
}

.jobs-list-enter-active {
}

.jobs-list-leave {
  opacity: 0;
  transform: translateX(30px);
}

.jobs-list-leave-active {
  transform: translateX(30px);
}

.jobs-list-leave-to {
  opacity: 0;
  transform: translateX(30px);
}

.board {
  min-width: 230px;
  min-height: 100px;
}

/*
  ## Device = 4k and ultra-wides
  ## Screen = > 1904px
*/
@media (min-width: 1904px) {
  .jobs {
    max-height: calc(100vh - 548px);
  }

  .board {
    height: calc(100vh - 435px);
  }
}

/*
  ## Device = Desktop
  ## Screen = 1281 > < 1904px
*/
@media (min-width: 1281px) and (max-width: 1904px) {
  .jobs {
    max-height: calc(100vh - 548px);
  }

  .board {
    height: calc(100vh - 435px);
  }
}

/*
  ## Device = Large tablet to laptop
  ## Screen = 960px > < 1264px
*/
@media (min-width: 960px) and (max-width: 1264px) {
  .jobs {
    max-height: calc(100vh - 548px);
  }

  .board {
    height: calc(100vh - 435px);
  }
}

/*
  ## Device = Small to medium tablet
  ## Screen = 600px > < 960px
*/
@media (min-width: 600px) and (max-width: 960px) {
  .jobs {
    max-height: calc(100vh - 236px);
  }

  .board {
    height: 100%;
  }
}

/*
  ## Device = Small to large handset
  ## Screen = < 600px
*/
@media (max-width: 600px) {
  .jobs {
    max-height: calc(100vh - 236px);
  }

  .board {
    height: auto;
  }
}
</style>
