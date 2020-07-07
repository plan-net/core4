<template>
  <v-dialog
    v-model="dialog"
    max-width="960px"
    min-height="400px"
  >

    <template v-slot:activator="{ on, attrs }">
      <v-btn
        fab
        dark
        small
        v-bind="attrs"
        v-on="on"
        xxxcolor="primary darken-1"
        color="secondary lighten-3"
      >
        <v-icon dark>add</v-icon>
      </v-btn>

    </template>
    <validation-observer
      ref="observer"
      v-slot="{  }"
    >
      <validation-provider
        v-slot="{ errors }"
        :rules="{ required: true, joberror: error}"
        name="Job"
      >
        <v-card id="job-card">
          <v-toolbar
            dense
            flat
            color="transparent"
          >

            <v-toolbar-title>Enqueue a job</v-toolbar-title>
            <v-spacer></v-spacer>
            <v-btn
              icon
              @click="dialog = false"
            >
              <v-icon large>close</v-icon>
            </v-btn>
          </v-toolbar>
          <v-card-text class="pt-0 pb-2">
            <v-form
              @submit.prevent="save"
              ref="form"
            >
              <v-row
                class="pt-5"
                align="center"
                justify="center"
              >
                <v-col
                  cols="12"
                  class="pb-6 pt-0"
                >
                  <select-2
                    :disabled="isLoading"
                    :value="model"
                    @input="onModelChange"
                    data-vv-name="Job"
                    :error-messages="errors"
                  />
                  <div
                    style="margin-top: -6px;"
                    class="error--text"
                  >{{ errors[0] }}</div>
                </v-col>
                <v-col
                  cols="12"
                  class="pt-0 pb-5"
                >
                  <args-editor
                    :disabled="isLoading"
                    @change="onArgsChange"
                  />

                </v-col>
                <v-col
                  cols="12"
                  class="pt-9"
                >
                  <v-btn
                    block
                    type="submit"
                    @keyup.enter.native="save"
                    large
                    :loading="isLoading"
                    :disabled="isLoading"
                    color="secondary lighten-3"
                  >
                    Enqueue
                    <template v-slot:loader>
                      <span class="custom-loader">
                        <v-icon
                          large
                          light
                        >cached</v-icon>
                      </span>
                    </template>
                  </v-btn>
                </v-col>
              </v-row>
            </v-form>
          </v-card-text>
        </v-card>
      </validation-provider>
    </validation-observer>

  </v-dialog>
</template>

<script>
// import api from '@//api/api2.js'
import yaml from 'js-yaml'
import ArgsEditor from '@/components/ArgsEditor.vue'
import { ValidationProvider, ValidationObserver, extend } from 'vee-validate'
import { mapState } from 'vuex'
import Select2 from '@/components/select2.vue'
extend('joberror', {
  validate: (value, { error }) => {
    if (error != null) {
      return false
    }
    return true
  },
  params: ['error'],
  message (val, val2) {
    return val2.error
  }
})
export default {
  components: {
    'select-2': Select2,
    ArgsEditor,
    ValidationProvider,
    ValidationObserver
  },

  data () {
    return {
      dialog: false,
      model: '',
      entries: [],
      isLoading: false,
      search: '',
      args: ''
    }
  },
  created () {
    window.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        this.save()
      }
    })
  },
  methods: {
    onArgsChange (args) {
      this.$store.dispatch('jobs/clearJobError')
      this.args = args
    },
    onModelChange ($event) {
      this.model = $event
      this.$store.dispatch('jobs/clearJobError')
    },

    async save (event) {
      if (event) {
        event.preventDefault()
      }

      this.$store.dispatch('jobs/clearJobError')
      // await this.$nextTick()
      this.$refs.observer.validate().then(async isValid => {
        if (isValid) {
          this.isLoading = true
          const ret = await this.$store.dispatch('jobs/enqueueJob', {
            job: this.model,
            args: yaml.safeLoad(this.args)
          })
          this.isLoading = false
          if (ret) {
            this.dialog = false
          }
        }
      })
    }
  },
  beforeDestroy () {
    window.removeEventListener('keydown', this.save)
  },
  watch: {
    open (newValue, oldValue) {
      if (newValue) {
        window.addEventListener('keydown', this.save.bind(this))
        this.$store.dispatch('jobs/clearJob')
      } else {
        window.removeEventListener('keydown', this.save)
      }
    }

  },
  computed: {
    ...mapState('jobs', [
      'error'
    ]),
    items () {
      return this.entries
    }
  }
}
</script>

<style lang="scss" scoped>
.custom-loader {
  animation: loader 1s infinite;
  display: flex;
}
@keyframes loader {
  from {
    transform: rotate(0);
  }
  to {
    transform: rotate(360deg);
  }
}
::v-deep .v-list-item__mask {
  color: white !important;
  //background: #FFCC00 !important;
  background: var(--v-primary-base) !important;
}
/* ::v-deep .v-dialog {
  position: absolute;
  top: 25px;
} */
</style>
