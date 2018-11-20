<template>
  <pnbi-page header-type="3" small>
    <!--    <div slot="page-header-content">
    </div> -->
    <pnbi-card :headline="$route.meta.title">
      <!-- Optional Slot-->
      <div slot="primary-controls">
        <v-layout>
            <v-select
              :items="questions"
              :value="question"
              @input="onChange"
              menu-props="auto"
              label="Fragen"
              item-text="question"
              item-value="session_id"
              hide-details
              prepend-icon="question_answer"
              return-object
              single-line
            ></v-select>
        </v-layout>
      </div>
      <!-- Default Slot-->
      <div>
        <pre>{{result}}</pre>
      </div>
      <!-- Optional Slot-->
      <div slot="card-actions">
      </div>
    </pnbi-card>

  </pnbi-page>
</template>
<script>
import {
  mapGetters,
  mapActions
} from 'vuex'
export default {
  components: {
  },
  created () {},
  methods: {
    ...mapActions(['fetchQuestions', 'setCurrentQuestion', 'setCurrentResult', 'fetchResult']),
    onChange (q) {
      this.setCurrentQuestion(q)
      this.setCurrentResult(q)
    }
  },
  mounted () {
    const currentSid = this.$route.params.sid
    this.fetchQuestions(currentSid)
    this.fetchResult(currentSid)
  },
  data () {
    return {
    }
  },
  watch: {
  },
  computed: {
    ...mapGetters(['question', 'questions', 'result'])
  }
}

</script>
