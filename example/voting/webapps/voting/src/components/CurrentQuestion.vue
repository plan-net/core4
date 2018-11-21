<template>
  <div>
    <v-layout v-if="question" column>
      <v-layout align-center justify-center row fill-height wrap>
        <v-flex xs12 lg10 class="question-container pt-5">
         <!--  <v-progress-linear :indeterminate="true"></v-progress-linear> -->

          <h2 class="display-3 white--text text-xs-center mb-3">
            {{question.question}}
            <v-tooltip right style="position: absolute;">
              <v-btn slot="activator" icon style="top: -6px;" @click="resetQuestion(question)">
                <v-icon style="opacity: .5" class="grey--text">clear</v-icon>
              </v-btn>
              <span>Zurücksetzen</span>
            </v-tooltip>
          </h2>
        </v-flex>
        <v-flex xs12 class="text-xs-center pt-3 mt-3">
          <percent></percent>
        </v-flex>
      </v-layout>
      <!-- <h3 class="display-2 white--text text-xs-center mb-3">{{question.seconds |seconds}}</h3> -->
      <!-- <h4 class="display-1 white--text text-xs-center mb-3">{{votes}} / {{peopleCount}}</h4> -->
      <!--       <pre>{{question}}</pre>
      <br> -->
      <!--       <v-layout align-center justify-end row fill-height>
        <v-flex xs3>
          <v-btn color="accent" small :to="`/result/${question.session_id}`" :disabled="question.state === 'OPEN'">
            Ergebnis
          </v-btn>
        </v-flex>
      </v-layout> -->
    </v-layout>
    <v-layout v-else></v-layout>
  </div>
</template>
<script>
import {
  mapGetters,
  mapActions
} from 'vuex'
import Percent from '@/components/Percent'
export default {
  components: {
    Percent
  },
  created () {},
  methods: {
    ...mapActions(['resetQuestion'])
  },
  mounted () {},

  data () {
    return {}
  },
  watch: {},
  computed: {
    ...mapGetters(['question', 'peopleCount']),
    votes () {
      try {
        return this.question.n || 0
      } catch (err) {}
      return 0
    }/* ,
    percent () {
      try {
        const p = this.question.n / this.peopleCount
        if (isNaN(p)) {
          throw new Error('No Number')
        }
        return (p * 100).toFixed(2)
      } catch (err) {}
      return 0
    } */
  }
}

</script>
<style lang="scss" scoped>
.question-container{
  position: relative;
  &:before{
    opacity: 0;
    position: absolute;
    top: -2px;
    content:'';
    width: 50%;
    left: 25%;
    height: 2px;
    background-color: rgba(255,255,255,.1);

  }
}
</style>
