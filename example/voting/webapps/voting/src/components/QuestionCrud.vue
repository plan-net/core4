<template>
  <pnbi-dialog :open="isOpen" @close="isOpen = false" width="60%" title="Frage erstellen / editieren">
    <div class="panel-body">
      <v-text-field v-if="question && question.session_id" label="Id" box disabled v-model="question.session_id"></v-text-field>

      <v-text-field required autofocus :error-messages="errors.collect('Frage')" data-vv-as="Frage" data-vv-name="Frage" v-validate="'required|min:2'" box label="Frage" v-model="internalData.question "></v-text-field>

      <v-textarea required box label="Data" placeholder="Valides Json: {label : 'Kurzvariante der Frage'}" v-model="internalData.data " :error-messages="errors.collect('Data')" data-vv-as="Data" data-vv-name="Data" v-validate="'required|json'"
      ></v-textarea>

      <!-- <pre>{{data}}</pre> -->
    </div>
    <div slot="dialog-actions">
      <v-btn color="primary" flat @click.native="isOpen = false">
        Abbrechen
      </v-btn>
      <v-btn color="primary" flat @click.native="save" :disabled="invalid">
        Speichern
      </v-btn>
    </div>

  </pnbi-dialog>
</template>

<script>
import {
  mapGetters
} from 'vuex'
export default {
  props: {
    open: {
      type: Boolean,
      default: false,
      required: true
    }
  },
  mounted () {
    // this.$validator.validateAll()
    this.setInitialData()
  },
  watch: {
    open (newValue) {
      if (newValue) {
        this.setInitialData()
      } else {
        this.internalData = {
          data: null,
          question: null
        }
        this.$validator.reset()
      }
    }
  },
  computed: {
    ...mapGetters(['question']),
    invalid () {
      return this.errors.any() || this.internalData.question == null || this.internalData.data == null
    },
    isOpen: {
      get: function (newVal) {
        return this.open
      },
      set: function (newVal) {
        this.$nextTick(function () {
          this.$emit('close')
        })
      }
    }
  },
  methods: {
    setInitialData () {
      if (this.question != null) {
        this.internalData = Object.assign({}, this.question)
        if (typeof this.internalData.data === 'object') {
          this.internalData.data = JSON.stringify(this.internalData.data)
        }
        this.$nextTick(function () {
          this.$validator.validateAll()
        })
      }
    },
    save () {
      this.$validator.validateAll().then(val => {
        if (val) {
          if ((this.question || {}).session_id != null) {
            this.internalData.session_id = this.question.session_id
          }
          this.$store.dispatch('saveQuestion', this.internalData)
          this.isOpen = false
        }
      })
    }
  },
  data () {
    return {
      internalData: {
        data: null,
        question: null
      }
    }
  }
}

</script>
<style scoped lang="scss">

</style>
