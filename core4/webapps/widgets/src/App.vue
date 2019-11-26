<template>
  <c4-webapp :full-width="true" :nav-button-visible="false">
    <div slot="router">
      <transition name="fade" mode="out-in" :duration="{ enter: 200, leave: 300 }">
        <router-view/>
      </transition>
    </div>
  </c4-webapp>
</template>
<script>
import { inIframe } from 'core4ui/core4/store/state'
import { mapGetters } from 'vuex'
export default {
  name: 'CORE4OS',
  watch: {
    authenticated (newValue, oldValue) {
      if (newValue === false) {
        this.$store.dispatch('clear')
      }
    }
  },
  computed: {
    ...mapGetters(['authenticated'])
  },
  mounted () {
    function bindEvent (element, eventName, eventHandler) {
      if (element.addEventListener) {
        element.addEventListener(eventName, eventHandler, false)
      } else if (element.attachEvent) {
        element.attachEvent('on' + eventName, eventHandler)
      }
    }
    if (inIframe() === false) {
      // this is coming from the iframe application!!!
      bindEvent(window, 'message', function (e) {
        if (e.data === 'c4-application-close') {
          this.$router.push('/')
        }
      }.bind(this))
    } else {
      this.$store.dispatch('setInWidget', true)
    };
  }
}
</script>
<style lang="scss">

</style>
