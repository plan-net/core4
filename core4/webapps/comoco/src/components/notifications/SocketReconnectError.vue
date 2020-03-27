<template>
  <div>
    Unable connect to the server. Please try <a @click="socketConnect">again later</a>.
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

      const token = JSON.parse(localStorage.getItem('user')).token
      this.$connect(`${getBasePath()}/event?token=${token}`)
    }
  }
}
</script>

<style scoped>
a {
  color: #ffffff;
  text-decoration: underline;
  cursor: pointer;
}
</style>
