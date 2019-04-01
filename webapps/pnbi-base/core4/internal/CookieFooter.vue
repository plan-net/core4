<template>
  <footer class="px-3 py-2" v-if="vis">
    <v-layout>
      <v-flex>

        <div>Wir verwenden
          <strong>Cookies</strong>, um die Aufrufe unserer Website zu analysieren.
          <br> Mit der Nutzung unserer Website erklären Sie sich damit einverstanden.</div>
      </v-flex>
      <v-layout>
        <v-flex class="mr-2">
          <v-btn flat block @click.stop="$emit('open-privacy-dialog')">Mehr Informationen</v-btn>
        </v-flex>
        <v-flex>
          <v-btn block color="primary" type="submit" @click.stop="onClick">Zustimmen</v-btn>
        </v-flex>
      </v-layout>
    </v-layout>
  </footer>
</template>

<script>
import CookieService from './cookie.service.js'
export default {
  created () {
    this.vis = typeof CookieService.isPriPolCookieSet() !== 'string'
  },
  methods: {
    onClick () {
      CookieService.setPriPolCookie()
      this.vis = false
    }
  },
  data () {
    return {
      vis: false
    }
  }
}

</script>

<style scoped>
</style>
