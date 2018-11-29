<template>
  <div>
    <pnbi-page header-type="3" small>
    <div style="overflow:hidden">
      <particles></particles>
    </div>
      <v-btn style="position: absolute; opacity: 0" :disabled="!question" color="accent" @click="dummyVote()">Vote</v-btn>

      <v-layout align-center justify-end row>
        <v-flex xs12 sm12 md10 lg8>
          <v-layout align-start justify-end>
            <v-btn large flat icon dark @click="prev">
              <v-icon large>keyboard_arrow_left</v-icon>
            </v-btn>
            <div class="pt-2">

              <v-btn small :disabled="!question" v-if="(question || {}).state === 'OPEN'" color="primary" @click="stopQuestion(question)">
                STOP</v-btn>
              <v-btn small :disabled="!question" v-else color="accent" @click="startQuestion(question)">START</v-btn>

            </div>
            <v-btn large flat icon dark @click="next">
              <v-icon large>keyboard_arrow_right</v-icon>
            </v-btn>
          </v-layout>
        </v-flex>
      </v-layout>
      <v-layout align-center justify-center>
        <v-flex xs12 class="pa-3 pt-5">
          <current-question></current-question>
        </v-flex>
      </v-layout>
      <h3 v-if="(question || {}).state === 'OPEN'" class="seconds display-1 white--text text-xs-center">{{question.seconds
        |seconds}}</h3>
    </pnbi-page>
  </div>
</template>
<script>
import CurrentQuestion from '@/components/CurrentQuestion'
import Particles from '@/components/Particles'
import {
  mapGetters,
  mapActions
} from 'vuex'
export default {
  components: {
    CurrentQuestion,
    Particles
  },
  filters: {
    seconds: function (value) {
      if (value != null) {
        let dSecs = ((value > 9 && value !== 0) ? value : '0' + value)
        return `${dSecs} Sekunden`
      }
      return '0 Sekunden'
    }
  },
  created () {},
  methods: {
    prevNext () {
      let index = 0
      try {
        this.questions.forEach((val, i) => {
          if (val.question === this.question.question) {
            index = i
          }
        })
      } catch (err) {

      }
      return new Promise(resolve => {
        if ((this.question || {}).state === 'OPEN') {
          this.stopQuestion().then(() => {
            this.$nextTick(function () {
              resolve(index)
            })
          })
        }
        resolve(index)
      })
    },
    next () {
      this.prevNext().then(currIndex => {
        const nextIndex = (currIndex === this.questions.length - 1) ? 0 : currIndex + 1
        const next = this.questions[nextIndex]
        this.setCurrentQuestion(next)
      })
    },
    prev () {
      this.prevNext().then(currIndex => {
        const prev = this.questions[(currIndex === 0) ? this.questions.length - 1 : currIndex - 1]
        this.setCurrentQuestion(prev)
      })
    },
    ...mapActions(['fetchQuestions', 'startQuestion', 'stopQuestion', 'resetQuestion', 'setCurrentQuestion',
      'dummyVote'
    ])
  },
  mounted () {
    const currentSid = this.$route.params.sid
    this.fetchQuestions(currentSid)
  },
  data () {
    return {}
  },
  watch: {
    percent () {
      this.particles = false
      this.$nextTick(function () {
        this.particles = true
      })
    }
  },
  beforeDestroy () {
    this.stopQuestion()
  },
  computed: {
    ...mapGetters(['question', 'questions', 'peopleCount']),
    percent () {
      try {
        const p = this.question.n / this.peopleCount
        if (isNaN(p)) {
          throw new Error('No Number')
        }
        const ret = Math.round(p * 100)
        return ret
      } catch (err) {}
      return 10
    }
  }
}

</script>
<style scoped lang="css">
  div>>>.gradient-1 {
    height: auto !important;
    background: linear-gradient(120deg, #2a373f 70%, #2f404a 70%);
  }

  div>>>.pnbi-page-header {
    display: none;
  }

  .seconds {
    position: fixed;
    bottom: 29px;
    right: 35px;
    opacity: .2;
  }

</style>
