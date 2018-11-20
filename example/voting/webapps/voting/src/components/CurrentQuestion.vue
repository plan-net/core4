<template>
  <div>
    <v-layout v-if="question" column>
      <hr>
      <br>
      <h2 class="headline">Frage: {{question.question}}</h2>
      <br>
      <h3 class="title">Zeit: {{question.seconds |seconds}}</h3>
      <br>
      <div>Stimmen: {{question.n}} / X</div>
      <br>
      <!--       <pre>{{question}}</pre>
      <br> -->
      <v-flex xs2>
        <v-btn color="primary" flat :to="`/result/${question.session_id}`" :disabled="question.state === 'OPEN'">
        Ergebnis
      </v-btn>
      </v-flex>
    </v-layout>
    <v-layout v-else></v-layout>
  </div>
</template>
<script>
import {
  mapGetters,
  mapActions
} from 'vuex'
export default {
  components: {},
  created () {},
  methods: {
    ...mapActions([])
  },
  mounted () {},
  filters: {
    seconds: function (value) {
      if (value != null) {
        let dSecs = (value > 9 ? value : '0' + value)
        return `${dSecs} Sekunden`
      }
    }
  },
  data () {
    return {}
  },
  watch: {

  },
  computed: {
    ...mapGetters(['question'])
  }
}

</script>
