<template>
  <v-container :fluid="false">
    <pnbi-page header-type="3" small>
      <!--       <v-layout align-center justify-end row>
        <v-flex xs12 sm12 md10 lg8>
          <v-layout align-start justify-end>
            <v-btn class="extra-large" flat icon dark @click="next">
              <v-icon style="font-size: 60px;">keyboard_arrow_right</v-icon>
            </v-btn>
          </v-layout>
        </v-flex>
      </v-layout> -->
      <v-layout row wrap class="mt-3" align-center justify-center>
        <v-flex xs8 v-for="(value, key) in clusteredResults" :key="key" class="pnbi-card">
          <div>
            <h3 class="title white--text text-xs-center pt-3">{{value.question.question}}</h3>
            <v-layout row class="chart-element" wrap>
              <v-flex xs3>
                <v-layout column align-center justify-end fill-height>
                  <v-flex>
                    chart
                  </v-flex>
                  <div class="legende">
                    m f
                  </div>
                </v-layout>
              </v-flex>
              <v-flex xs3>
                <v-layout column align-center justify-end fill-height>
                  <v-flex>
                    chart
                  </v-flex>
                  <div class="legende">
                    m f
                  </div>
                </v-layout>
              </v-flex>
              <v-flex xs3>
                <v-layout column align-center justify-end fill-height>
                  <v-flex>
                    chart
                  </v-flex>
                  <div class="legende">
                    m f
                  </div>
                </v-layout>
              </v-flex>
              <v-flex xs3>
                <v-layout column align-center justify-end fill-height>
                  <v-flex>
                    chart
                  </v-flex>
                  <div class="legende">
                    m f
                  </div>
                </v-layout>
              </v-flex>
            </v-layout>
          </div>
          <v-btn fab dark large color="primary" class="next-btn">
            <v-icon large dark>keyboard_arrow_right</v-icon>
          </v-btn>
        </v-flex>
      </v-layout>
    </pnbi-page>
  </v-container>

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
    ...mapActions(['fetchQuestions', 'setCurrentQuestion', 'setCurrentResult', 'fetchResult']),
    next (q) {
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
    return {}
  },
  watch: {},
  computed: {
    ...mapGetters(['question', 'questions', 'result', 'peopleCount', 'clusteredResults'])
  }
}

</script>
<style scoped lang="css">
  div>>>.extra-large {
    width: 60px;
    height: 60px;
  }

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

  .pnbi-card {
    padding: 8px;
  }

</style>
<style scoped lang="scss">
  $k-height: 600px;
  $k-height2: $k-height/2 - 20px;

  .pnbi-card {
    padding: 8px;
    position: relative;

    .next-btn {
      top: $k-height2;
      right: -35px;
      position: absolute;
    }
  }

  .pnbi-card>div {
    height: $k-height;
    background-color: #364650;
  }

  .chart-element {
    height: calc(100% - 45px);
    position: relative;

    .legende {
      text-align: center;
      bottom: 0;
      color: #fff;
      text-align: center;
      border: 1px solid white;
      width: inherit;
    }

    >div {
      // border: 1px solid rgba(255,255,255,.05);
    }
  }

</style>
