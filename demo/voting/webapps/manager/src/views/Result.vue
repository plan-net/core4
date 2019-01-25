<template>
  <v-container :fluid="false">
    <pnbi-page
      header-type="3"
      small
      v-if="timeout"
    >
      <v-layout
        row
        wrap
        class="mt-3"
        align-center
        justify-center
      >

        <v-carousel
          hide-delimiters
          :hide-controls="hideControls"
          height="100%"
          :cycle="false"
        >
          <v-carousel-item
            v-for="(value, key) in iChartsOptions"
            :key="key"
          >
            <div>
              <h3 class="title white--text text-xs-center pt-5">{{value.question.question}}</h3>
              <v-layout
                column
                class="chart-element"
              >
                <v-flex xs12>
                  <v-layout
                    column
                    align-center
                    justify-end
                    fill-height
                  >
                    <v-flex class="pt-5">
                      <chart :options="value"></chart>
                    </v-flex>
                  </v-layout>
                </v-flex>
                <v-flex xs12>
                  <v-layout
                    column
                    align-center
                    justify-end
                    fill-height
                  >
                    <v-flex
                      xs12
                      class="pt-5"
                    >
                      <chart :options="iChartsOptionsAge[key]"></chart>
                    </v-flex>
                  </v-layout>
                </v-flex>
              </v-layout>
              <v-layout class="pt-3 detail-container">
                <v-flex xs12>
                  <h4 class="subheading white--text">Wer hat abgestimmt?</h4>
                  <div class="pa-2 white--text"
                    v-for="(person, key2) in detail"
                    :key="key2"
                  >
                    {{person.realname}}   <v-icon class="primary--text">sentiment_very_satisfied</v-icon>
                  </div>
                </v-flex>
              </v-layout>
            </div>
          </v-carousel-item>
        </v-carousel>
      </v-layout>
    </pnbi-page>
  </v-container>

</template>
<script>
import { Chart } from 'highcharts-vue'
import { getChartTemplate } from './chart-config.js'
import {
  mapGetters,
  mapActions
} from 'vuex'
export default {
  components: {
    Chart
  },
  methods: {
    ...mapActions(['fetchQuestions', 'setCurrentQuestion', 'setCurrentResult', 'fetchResult']),
    next (q) {
      this.setCurrentQuestion(q)
      // not ussed for now!!!
      // this.setCurrentResult(q)
    },
    gotoNextQuestion () {
      console.log('item', this.iChartsOptions2)
    }
  },
  mounted () {
    // const currentSid = this.$route.params.sid
    this.fetchQuestions()
    // highcharts-vue is a piece of shit
    // it took me 2 hours in the evening to show
    // the fucking chart with this bullshit
    // on reload chart was not there
    // use vue-highcharts (maybe, better test)
    window.setTimeout(function () {
      this.fetchResult()
    }.bind(this), 100)
    window.setTimeout(function () {
      this.fetchResult()
    }.bind(this), 200)
    window.setTimeout(function () {
      this.timeout = true
    }.bind(this), 300)
  },
  data () {
    return {
      timeout: null
    }
  },
  watch: {},
  computed: {
    hideControls () {
      if (this.clusteredResults) {
        return this.clusteredResults.length <= 1
      }
      return true
    },
    iChartsOptions () {
    // not working in dev reload page
    // beacuase fetch only on mounted
      if (this.clusteredResults) {
        const tmp = this.clusteredResults.map(val => {
          const tplPlusSeries = getChartTemplate()
          tplPlusSeries.series = { data: val.sex }
          tplPlusSeries.xAxis.categories = ['Männer', 'Frauen']
          tplPlusSeries.title.text = 'Nach Geschlecht'
          tplPlusSeries.question = val.question
          return tplPlusSeries
        })
        return tmp
      }
      return null
    },
    detail () {
      if (this.clusteredResults != null) {
        console.log(this.clusteredResults)
        return this.clusteredResults[0].detail // first question resultset
      }
      return []
    },
    iChartsOptionsAge () {
    // not working in dev reload page
    // beacuase fetch only on mounted
      if (this.clusteredResults) {
        const tmp = this.clusteredResults.map(val => {
          const tplPlusSeries = getChartTemplate()
          tplPlusSeries.series = { data: val.age }
          tplPlusSeries.xAxis.categories = ['Unter 30', 'Über 30']
          tplPlusSeries.title.text = 'Nach Alter'
          tplPlusSeries.question = val.question
          return tplPlusSeries
        })
        return tmp
      }
      return null
    },
    ...mapGetters(['question', 'questions', 'result', 'peopleCount', 'clusteredResults'])
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
</style>
<style scoped lang="scss">
  .v-carousel {
    background-color: #364650;
  }
  .title {
    font-size: 30px !important;
  }
  $k-height: 1000px;
  $k-height2: $k-height/2 - 20px;

  .pnbi-card {
    padding: 8px;
    position: relative;
    .next-btn {
    }
  }

  .pnbi-card>div {
    height: auto;
    background-color: #364650;
  }

  .chart-element {
    height: 100%;
    position: relative;
    >div {
    }
  }
  .detail-container{
    padding-bottom: 16px;
    .subheading{
      width: 100%;
      text-align: center;
      margin-bottom: 12px;

    }
    width: 100%;
    max-width: 1000px;
    margin: 0 auto;
  }

</style>
