<template>
  <v-dialog
    scrollable
    max-width="720"
    v-model="open"
    persistent
  >
    <v-card
      tile
      class="pa-0"
    >
      <template v-if="alertMessage">
        <v-toolbar
          class="px-0"
          dense
          card
          color="error"
        >
          <v-toolbar-title>
            ERROR
          </v-toolbar-title>
          <v-spacer></v-spacer>
        </v-toolbar>
        <v-card-text class="px-4 py-3">

          <p
            v-if="alertMessage.html"
            v-html="alertMessage.html"
          ></p>
          <div v-if="alertMessage.json">
            <pre class="mt-2 pa-1">{{alertMessage.json}}</pre>
          </div>
          <div v-else>
            <pre class="mt-2 pa-1">{{alertMessage.data}}</pre>
          </div>
        </v-card-text>
        <v-card-actions class="pl-3 pr-3 pb-3 pt-0">
          <v-spacer></v-spacer>
          <v-btn
            type="button"
            alertMessage.status_code
            v-if="alertMessage.status_code === 401 || alertMessage.status_code === 403"
            @click="logout(); open = false"
            color="primary"
          >
            Zum Login
          </v-btn>
          <v-btn
            type="button"
            v-else
            @click="open = false"
            color="primary"
          >
            OK
          </v-btn>
        </v-card-actions>

      </template>
    </v-card>
  </v-dialog>

</template>
<script>
import {
  mapGetters,
  mapActions
} from 'vuex'
export default {
  mixins: [],
  props: {},
  created () {},
  mounted () {
  },
  computed: {
    ...mapGetters([
      'error'
    ])
  },
  watch: {
    error: function (newVal) {
      if (newVal != null) {
        this.alertMessage = newVal
        this.open = true
        this.hideError()
      }
    }
  },
  data () {
    return {
      alertMessage: null,
      open: false
    }
  },
  methods: {
    ...mapActions(['hideError', 'logout'])
  }
}
</script>

<style scoped lang="scss">
</style>
