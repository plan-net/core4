<template>
  <v-dialog v-model="dialog">

    <v-card class="pb-5 pt-1">
      <v-toolbar
        class="pl-5"
        flat
        color="transparent"
      >
        <v-row class="qualname">
          <div>

            <h5 class="grey--text">Qualname</h5>
            <h2>{{job.qual_name || job.name}}
              <v-btn
                style="margin-top: -4px;"
                icon
                small
                @click="copy(job.qual_name || job.name)"
              >
                <v-icon small>mdi-content-copy</v-icon>
              </v-btn>
            </h2>
          </div>
          <h2 class="job-count">{{jobs.length}}</h2>
        </v-row>
        <v-spacer></v-spacer>
        <v-btn
          icon
          @click="close()"
        >
          <v-icon large>mdi-close</v-icon>
        </v-btn>
      </v-toolbar>
      <v-card-text>

        <v-row>
          <v-col cols="12">

            <v-data-table
              class="job-dt elevation-1"
              dense
              v-model="internalJob"
              single-select
              :headers="headers"
              item-key="_id"
              xxxshow-select
              :item-class="itemClass"
              :items="internalJobs"
              :loading="loading"
              single-expand
              :expanded.sync="internalJob"
              :server-items-length="totalJobs"
              :options.sync="options"
              :footer-props="{itemsPerPageOptions:jobRowsPerPageItems}"
              show-expand
            >
              <template v-slot:expanded-item="{ headers }">
                <td
                  :colspan="headers.length"
                  class="px-0 pt-0 pb-6"
                >
                  <v-row>
                    <v-col
                      cols="10"
                      class="pr-1 pl-8 pb-0 pt-4"
                    >
                      <v-tabs v-model="tabs">
                        <v-tab>Log</v-tab>
                        <v-tab>Args</v-tab>
                      </v-tabs>
                      <v-tabs-items v-model="tabs">
                        <v-tab-item>
                          <v-textarea
                            rows="12"
                            filled
                            :dark="$store.getters.dark"
                            label=""
                            :value="internalLogMessage"
                            readonly
                          ></v-textarea>

                        </v-tab-item>
                        <v-tab-item>
                          <args-display
                            v-if="tabs === 1"
                            :job-id="internalJob[0]._id"
                          ></args-display>
                        </v-tab-item>
                      </v-tabs-items>
                    </v-col>
                    <v-col
                      cols="2"
                      justify="center"
                      align="center"
                      class="pr-6"
                      style="margin-top:65px;"
                    >
                      <job-managment-buttons :job-count="jobs.length" />
                    </v-col>
                  </v-row>
                </td>
              </template>
              <template v-slot:item._id="{ item }">
                {{ item._id }}
                <v-btn
                  icon
                  small
                  @click="copy(item._id)"
                >
                  <v-icon small>mdi-content-copy</v-icon>
                </v-btn>
              </template>
              <template v-slot:item.state="{ item }">
               {{item.$removed ? '-': item.state}}
              </template>
              <template v-slot:item.started_at="{ item }">
                {{ item.started_at | date }}
              </template>
              <template v-slot:item.enqueued="{ item }">
                {{ item.enqueued.username }}
              </template>
              <template v-slot:item.runtime="{ item }">
                <template v-if="item.runtime">
                  {{ item.runtime | number }}
                </template>
                <template v-else>
                  ?
                </template>
              </template>
              <template v-slot:item.prog="{ item }">
                <template v-if="item.prog.value">
                  {{ item.prog.value * 100 | number }}%
                </template>
                <template v-else>
                  ?
                </template>
              </template>
            </v-data-table>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script>
import _ from 'lodash'
import JobManagmentButtons from '@/components/job/JobManagmentButtons.vue'
import ArgsDisplay from '@/components/ArgsDisplay.vue'
// import JobStateFilter from '@/components/job/JobStateFilter.vue'
import { mapGetters } from 'vuex'
let ti
const headers = [
  {
    text: 'JobId',
    align: 'start',
    sortable: false,
    value: '_id'
  },
  {
    text: 'State',
    align: 'start',
    sortable: false,
    value: 'state'
  },
  {
    text: 'Username',
    align: 'start',
    sortable: false,
    value: 'enqueued'
  },
  {
    text: 'Started',
    align: 'end',
    sortable: false,
    value: 'started_at'
  },
  {
    text: 'Runtime (sek)',
    align: 'end',
    sortable: false,
    value: 'runtime'
  },
  {
    text: 'Progress',
    align: 'end',
    sortable: false,
    value: 'prog'
  }
]
export default {

  props: {
    jobDetailDialogOpen: {
      type: Boolean,
      default: false,
      required: true
    }
  },
  filters: {
    number: function (value) {
      const formatConfig = {
        maximumFractionDigits: 2,
        minimumFractionDigits: 1
      }
      if (value != null) {
        return new Intl.NumberFormat('de-DE', formatConfig).format(value)
      }
      return value
    },
    date: function (value) {
      const options = { year: '2-digit', month: 'numeric', day: 'numeric', hour: 'numeric', minute: 'numeric', second: 'numeric' }
      return new Date(value).toLocaleDateString('de-DE', options)
    }
  },
  components: {
    JobManagmentButtons,
    // JobStateFilter,
    ArgsDisplay
  },
  data () {
    return {
      tabs: null,
      headers,
      expanded: null,
      options: {},
      loading: false
    }
  },

  methods: {
    itemClass (val) {
      if (val.$removed) {
        return 'black-border'
      }
      const c1 = val.state + '-border'
      return c1
    },
    copy (text) {
      window.navigator.clipboard.writeText(
        text || this.job.qual_name || this.job.name
      )
    },
    close () {
      this.$store.dispatch('jobs/clearJob', true)
    },
    throttledLoad: _.debounce(function () {
      this.load()
    }, 500),
    async load () {
      this.loading = true
      await this.$nextTick()
      await this.$store.dispatch('jobs/fetchJobsByName', {
        options: this.options,
        job: this.job
      })
      this.loading = false
    }
  },
  mounted () {
  },
  watch: {
    options: {
      handler () {
        this.throttledLoad()
      },
      deep: true
    },
    jobDetailDialogOpen (newValue, oldValue) {
      if (newValue) {
        this.throttledLoad()
      }
    },
    internalLogMessage (newVal) {
      if (newVal != null && newVal.length > 200) {
        clearTimeout(ti)
        ti = setTimeout(() => {
          try {
            const textarea = document.querySelector('.job-dt').querySelector('textarea')
            textarea.scrollTop = textarea.scrollHeight
          } catch (err) {}
        }, 1)
      }
    }
  },
  computed: {
    ...mapGetters('jobs', [
      'job', 'log', 'jobs', 'filter',
      'filteredJobs', 'jobRowsPerPageItems', 'totalJobs'
    ]),
    id () {
      return this.job._id
    },
    internalLogMessage () {
      return this.log
    },
    internalJobs () {
      return this.filteredJobs.map(val => {
        return Object.assign(val, { isSelectable: val._id !== this.job._id })
      })
    },
    dialog: {
      // selected job in datatable
      get () {
        return this.jobDetailDialogOpen
      },
      set (newVal) {
        console.log(newVal)
        if (newVal === false) {
          this.close()
        }
      }
    },
    internalJob: {
      // selected job in datatable
      get () {
        return [this.job]
      },
      set (newVal) {
        if ((newVal || []).length > 0) {
          if (newVal[0]._id !== this.job._id) {
            this.$store.dispatch('jobs/setJob', newVal[0])
          }
        }
      }
    }
  }
}
</script>
<style lang="css">
tr.prog {
  position: relative;
  box-shadow: 0px 24px 3px -24px magenta !important;
}
</style>
<style lang="scss" scoped>
.job-count {
  margin-top: 2px;
  padding-left: 12px;
  font-weight: 700;
  font-size: 40px;
}
/* ::v-deep tr.v-data-table__selected {
  background: transparent !important;
} */
.qualname {
  h5,
  h2 {
    line-height: 1;
  }
}
::v-deep .v-card {
  height: 100%;
}
::v-deep .v-dialog {
  width: calc(100% - 60px);
  max-width: calc(100% - 20px);
  position: absolute;
  left: 10px;
  right: 10px;
  top: 10px;
}
/*TODO: import {jobColors} from '@/.../settings.js */
::v-deep {
  .v-textarea {
    font-family: monospace !important;
    textarea {
      font-size: 13px !important;
      line-height: 15px !important;
    }
  }
  .black-border td {
    color: grey !important;
    text-decoration: line-through;
  }
  .black-border td:first-child {
    border-left: 7px solid #010101 !important;
     text-decoration: none;
  }
  .pending-border td:first-child {
    border-left: 7px solid #ffc107 !important;
  }
  .deferred-border td:first-child {
    border-left: 7px solid #f1f128 !important;
  }
  .failed-border td:first-child {
    border-left: 7px solid #11dea2 !important;
  }
  .running-border td:first-child {
    border-left: 7px solid #64a505 !important;
  }
  .error-border td:first-child {
    border-left: 7px solid #d70f14 !important;
  }
  .inactive-border td:first-child {
    border-left: 7px solid #8d1407 !important;
  }
  .killed-border td:first-child {
    border-left: 7px solid #d8c9c7 !important;
  }
  .theme--light {
    .complete-border {
      td:first-child {
        border-left: 7px dashed rgba(0, 0, 0, 0.87) !important;
      }
      //background-color: rgba(0, 0, 0, 0.5) !important;
    }
  }
  .theme--dark {
    .complete-border {
      td:first-child {
        border-left: 7px dashed rgba(255, 255, 255, 1) !important;
      }
      //background-color: rgba(0, 0, 0, 0.5) !important;
    }
  }
}

/*   .pending: '#ffc107',
  .deferred: '#f1f128',
  .failed: '#11dea2',
  .running: '#64a505',
  .error: '#d70f14',
  .inactive: '#8d1407',
  .killed: '#d8c9c7' */
</style>
