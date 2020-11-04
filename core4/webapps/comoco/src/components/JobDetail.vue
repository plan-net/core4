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
            <h2>{{job.name}}
              <v-btn
                style="margin-top: -4px;"
                icon
                small
                @click="copy(job.name)"
              >
                <v-icon small>mdi-content-copy</v-icon>
              </v-btn>
            </h2>
          </div>
          <h2 class="job-count">{{jobs.length}}</h2>
        </v-row>
        <job-state-filter v-if="jobs.length" />
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
              dense
              v-model="internalJob"
              single-select
              :headers="headers"
              item-key="_id"
              xxxshow-select
              :item-class="itemClass"
              :items="internalJobs"
              xxxclass="elevation-1"
              :hide-default-footer="jobs.length < 10"
              single-expand
              :expanded.sync="internalJob"
              show-expand
            >
              <template v-slot:expanded-item="{ headers }">
                <td
                  :colspan="headers.length"
                  class="px-0 py-0"
                >
                  <v-row>
                    <v-col
                      cols="10"
                      class="pr-1 pl-8 py-0"
                    >
                      <!--                  <ace-editor
                        disabled
                        :height="'400px'"
                        label="Log"
                        language="rdoc"
                        font-family="monospace"
                        :value="internalLogMessage"
                      /> -->
                      <v-textarea
                      auto-grow
                        filled
                        :dark="$store.getters.dark"
                        label=""
                        :value="internalLogMessage"
                        readonly
                      ></v-textarea>
                    </v-col>
                    <v-col
                      cols="2"
                      justify="center"
                      align="center"
                      class="pr-6"
                      style="margin-top:100px;"
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
import JobManagmentButtons from '@/components/job/JobManagmentButtons.vue'
import JobStateFilter from '@/components/job/JobStateFilter.vue'
import { mapGetters } from 'vuex'

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
/* let int
const adjustProg = () => {
  const prog = document.querySelectorAll('.prog')
  prog.forEach(val => {
    let progress = val.className.substring(val.className.indexOf('prog-') + 5)
    progress = Number(progress) * 100

         const td = val.querySelector('td')
    td.setAttribute('data-width', `${progress}%`)
  })
} */
export default {
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
    JobStateFilter
  },
  data () {
    return {
      dialog: false,
      headers,
      expanded: null
    }
  },
  beforeDestroy () {

  },
  methods: {
    itemClass (val) {
      const c1 = val.state + '-border'
      /*      const prog = val.prog.value
      let c2 = ''
      if (prog) {
        c2 = ' prog prog-' + prog
      } */
      return c1 // + c2
    },
    copy (text) {
      text = text || this.job.name
      window.navigator.clipboard.writeText(text)
    },
    close () {
      this.$store.dispatch('jobs/clearJob', true)
      /*       await this.$nextTick()
      this.dialog = false */
    }
  },
  mounted () {
  },
  watch: {
    jobsAvail (newValue, oldValue) {
      if (newValue === false) {
        this.dialog = false
        this.$nextTick(function () {
          this.close()
        })
      } else {
        this.dialog = true
      }
    }
  },
  computed: {
    jobsAvail () {
      return this.jobs.length > 0
    },
    /*     jobs () {
      return this.$store.getters.filteredJobs
    }, */
    ...mapGetters('jobs', [
      'job', 'log', 'jobs', 'filter', 'filteredJobs'
    ]),
    id () {
      return this.job._id
    },
    internalLogMessage () {
      return this.log// .map(val => val.date + ' | ' + val.message).join('\n')
    },
    internalJobs () {
      return this.filteredJobs.map(val => {
        return Object.assign(val, { isSelectable: val._id !== this.job._id })
      })
    },
    internalJob: {
      // selected job in datatable
      get () {
        return [this.job]
      },
      set (newVal) {
        if (newVal[0]._id !== this.job._id) {
          this.$store.dispatch('jobs/setJob', newVal[0])
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
    textarea{

    font-size: 13px !important;
    line-height: 15px !important;
    }
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
