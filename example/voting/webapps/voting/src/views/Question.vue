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
              @input="setCurrentQuestion"
              menu-props="auto"
              label="Fragen"
              item-text="question"
              item-value="session_id"
              hide-details
              prepend-icon="question_answer"
              return-object
              single-line
            ></v-select>
            <v-btn :disabled="!question" v-if="(question || {}).state === 'OPEN'" color="primary" @click="stopQuestion(question)">Frage stoppen</v-btn>
            <v-btn :disabled="!question"  v-else color="primary" @click="startQuestion(question)">Frage starten</v-btn>
            <v-btn :disabled="!question" color="accent" @click="dummyVote()">Vote</v-btn>
        </v-layout>
      </div>
      <!-- Default Slot-->
      <div>
        <!-- <pre>{{question}}</pre> -->
        <current-question></current-question>
      </div>
      <!-- Optional Slot-->
      <div slot="card-actions">
      </div>
    </pnbi-card>

  </pnbi-page>
</template>
<script>
import CurrentQuestion from '@/components/CurrentQuestion'
import {
  mapGetters,
  mapActions
} from 'vuex'
export default {
  components: {
    CurrentQuestion
  },
  created () {},
  methods: {
    ...mapActions(['fetchQuestions', 'startQuestion', 'stopQuestion', 'setCurrentQuestion', 'dummyVote'])
  },
  mounted () {
    const currentSid = this.$route.params.sid
    this.fetchQuestions(currentSid)
  },
  data () {
    return {
    }
  },
  watch: {
    /*     question (newVal, oldVal) {
      if (oldVal != null && oldVal.state === 'OPEN') {
        this.stopQuestion(oldVal)
      }
    } */
  },
  beforeDestroy () {
    this.stopQuestion()
  },
  computed: {
    ...mapGetters(['question', 'questions'])
  }
}

</script>
