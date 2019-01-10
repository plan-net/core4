<template>
  <pnbi-page header-type="3" large>
    <v-btn fab dark large fixed color="primary" @click="vote">
      <v-icon dark large>add</v-icon>
    </v-btn>
    <div class="text-container">
      <h5 class="title">Willkommen in der Voting App</h5>
      <p>Wenn du der aktuelen Frage zustimmst, dann klicke auf den Plus-Button,
      oder hebe die Hand mit deinem Handy.
      </p>
<!--       <pre style="font-size: 24px; color: white;">{{maxAcc}}</pre>
      <pre style="font-size: 24px; color: white;">{{dump2}}</pre> -->
    </div>
  </pnbi-page>
</template>
<script>
/* import {
  mapGetters,
  mapActions
} from 'vuex' */
import api from '@/api/api'
// import * as FULLTILT from '@/libs/gyronorm.complete.js'
// import GyroNorm from 'gyronorm'
export default {
  name: 'user-voting',
  components: {
  },
  created () {
    // this.gn = new GyroNorm()
    // console.log(FULLTILT)
    const me = this.$route.params.uid || ''
    api.register(me)
  },
  mounted () {
    if (window.DeviceMotionEvent != null) {
      window.ondevicemotion = function (e) {
        const ax = e.acceleration.x
        const ay = e.acceleration.y
        const az = e.acceleration.z
        this.maxAcc = Math.max(Math.abs(ax), Math.abs(ay), Math.abs(az))
      }.bind(this)
      window.setInterval(function () {
        if (this.maxAcc > 1.8 && this.blocked === false) {
          if (this.streak > 20) {
            this.streak = 0

            this.vote()
          }
          this.streak++
        } else {
          this.streak = 0
        }
      }.bind(this), 25)
    }
  },
  methods: {
    vote () {
      this.blocked = true
      this.maxAcc = 0
      this.streak = 0
      const me = this.$route.params.uid || ''
      api.vote(me).then(() => {
        this.$store.dispatch('showNotification', {
          text: 'Gewählt.'
        })
        window.setTimeout(function () {
          this.blocked = false
        }.bind(this), 5000)
      }).catch(err => {
        console.error(err)
        this.$store.dispatch('showNotification', {
          text: 'Abstimmung nicht mehr möglich.',
          type: 'error'
        })
      })
    }
  },
  data () {
    return {
      gn: null,
      maxAcc: 0,
      streak: 0,
      blocked: false
    }
  },
  computed: {
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
  div >>> .v-btn--floating.v-btn--large{
    height: 96px;
    width: 96px;
    left: calc(50vw - 48px);
    top: calc(15vh);
  }
  div >>> .v-btn--floating.v-btn--large .v-icon{
    font-size: 60px !important;
  }
  h5, p{
    color: #fff;
  }
  h5{
    margin-bottom:12px;
  }
  .text-container{
    padding: 4px;
    left:5vw;
    position:fixed;
    top: calc(15vh + 124px);
    width: 90vw;
    text-align: center;
  }
</style>
