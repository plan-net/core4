<template>
  <v-container class="board">

    <!-- Group info (counter all of jobs with the same states) -->
    <info :name="name" :states="states"></info>

    <v-layout column class="jobs">

      <!-- list of all jobs which belongs to this group -->
      <v-flex v-for="(job, index) in getJobsByGroupName(name)" :key="index">
        <job :flags="flags" :job="job"></job>
      </v-flex>

    </v-layout>
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
@import '../style/comoco';

$scrollbar-track: #4A4A4A;
$scrollbar-thumb: #5C5C5C;
$scrollbar-thumb-hover: #737373;

.board {
  background-color: $jobs-board-bck-color;
  min-width: 230px;
  height: 100%;
}

.jobs {
  overflow-y: auto;
  overflow-x: hidden;

  &::-webkit-scrollbar-track {
    background-color: $scrollbar-track;
  }

  &::-webkit-scrollbar {
    width: 5px;
    background-color: transparent;
  }

  &::-webkit-scrollbar-thumb {
    background-color: $scrollbar-thumb;
  }

  &:hover::-webkit-scrollbar-thumb {
    background-color: $scrollbar-thumb-hover;
  }
}

/*
  ## Device = 4k and ultra-wides
  ## Screen = > 1904px
*/
@media (min-width: 1281px)and (max-width: 1904px) {
  .jobs {
    max-height: calc(100vh - 220px); /* -620px size with chart */
  }
}

/*
  ## Device = Desktop
  ## Screen = 1264 > < 1904px
*/
@media (min-width: 1281px)and (max-width: 1904px) {
  .jobs {
    max-height: calc(100vh - 220px); /* -620px size with chart */
  }
}

/*
  ## Device = Large tablet to laptop
  ## Screen = 960px > < 1264px
*/
@media (min-width: 960px) and (max-width: 1264px) {
  .jobs {
    max-height: calc(100vh - 220px); /* -620px size with chart */
  }
}

/*
  ## Device = Small to medium tablet
  ## Screen = 600px > < 960px
*/
@media (min-width: 600px) and (max-width: 960px) {
  .jobs {
    max-height: calc(100vh - 220px);
  }
}

/*
  ## Device = Small to large handset
  ## Screen = < 600px
*/
@media (max-width: 600px) {
  .jobs {
    max-height: calc(100vh - 220px);
  }
}
</style>
