<template>
  <v-container :fluid="false">
    <pnbi-page header-type="3" small v-if="timeout">
      <v-layout row wrap class="mt-3" align-center justify-center >

        <v-carousel hide-delimiters height="1000" :cycle="false">
          <v-carousel-item
            v-for="(value, key) in iChartsOptions"
            :key="key">
            <div>
              <h3 class="title white--text text-xs-center pt-5">{{value.question.question}}</h3>

              <v-layout column class="chart-element">
                <v-flex xs12>
                  <v-layout column align-center justify-end fill-height>
                    <v-flex class="pt-5">
                      <chart :options="value"></chart>
                    </v-flex>
                  </v-layout>
                </v-flex>
                <v-flex xs12>
                  <v-layout column align-center justify-end fill-height>
                    <v-flex xs12 class="pt-5">
                      <chart :options="iChartsOptionsCountrys[key]"></chart>
                    </v-flex>
                  </v-layout>
                </v-flex>
              </v-layout>
            </div>
          </v-carousel-item>
        </v-carousel>

      </v-layout>
      <!-- <pre class="white--text">{{clusteredResults[1].result}}</pre> -->
    <!--   <pre>{{chartsOptions}}</pre> -->
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
    // use vue-highcharts (maybe, beeter test)
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
    iChartsOptions () {
    // not working in dev reload page
    // beacuase fetch only on mounted
      if (this.clusteredResults) {
        const tmp = this.clusteredResults.map(val => {
          const tplPlusSeries = getChartTemplate()
          tplPlusSeries.series = { data: val.sex }
          tplPlusSeries.xAxis.categories = ['Male', 'Female']
          tplPlusSeries.title.text = 'By sex'
          tplPlusSeries.question = val.question
          return tplPlusSeries
        })
        return tmp
      }
      return null
    },
    iChartsOptionsCountrys () {
    // not working in dev reload page
    // beacuase fetch only on mounted
      if (this.clusteredResults) {
        const tmp = this.clusteredResults.map(val => {
          const tplPlusSeries = getChartTemplate()
          tplPlusSeries.series = { data: val.countries.series }
          tplPlusSeries.xAxis.categories = val.countries.categories
          tplPlusSeries.question = val.question
          tplPlusSeries.title.text = 'By nationality'
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
    // height: 60vh;
    // padding-top: 20%;

    .next-btn {
      // display: none;
/*       top: $k-height2;
      right: -35px;
      position: absolute; */
    }
  }

  .pnbi-card>div {
    height: auto;
    background-color: #364650;
  }

  .chart-element {
    height: 100%;
    position: relative;

/*     .legende {
      text-align: center;
      bottom: 0;
      color: #fff;
      text-align: center;
      border: 1px solid white;
      width: inherit;
    } */
    >div {
      // border: 1px solid rgba(255,255,255,.05);
    }
  }

</style>
