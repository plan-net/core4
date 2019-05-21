<template>
  <div>
    Unable connect to the server. Please try <a @click="socketConnect">again</a>.
  </div>
<!--  <v-btn color="primary" @click="socketConnect">Try Again</v-btn>-->
</template>

<script>
import { getBasePath } from '../../helper'

export default {
  name: 'socket-reconnect-error',
  data () {
    return {}
  },
  methods: {
    socketConnect () {
      this.$disconnect()

      let token = JSON.parse(localStorage.getItem('user'))['token']
      this.$connect(`${getBasePath()}/event?token=${token}`)
    }
  }
}
</script>

<style scoped>
a {
  color: #FFFFFF;
  text-decoration: underline;
  cursor: pointer;
}
</style>
