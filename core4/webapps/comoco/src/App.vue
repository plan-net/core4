<template>
  <c4-webapp :full-width="true">
    <template slot="title-slot">
      <span class="p-headline">COMOCO</span>
    </template>
  </c4-webapp>
</template>

<script>
import { mapGetters } from 'vuex'
import { getBasePath } from './helper'

export default {
  name: 'Comoco',
  components: {},
  computed: {
    ...mapGetters(['authenticated'])
  },
  mounted () {
    console.log(this.$vuetify)
  },
  watch: {
    authenticated (newValue, oldValue) {
      this.$disconnect()
      if (newValue && newValue !== oldValue) {
        const token = JSON.parse(localStorage.getItem('user')).token
        this.$connect(`${getBasePath()}/event?token=${token}`)
      }
    }
  }
}
</script>

<style scoped lang="scss">
::v-deep .layout.c4-page {
  padding-top: 12px !important;
}
::v-deep .ace_editor {
  border: 1px solid rgba(0, 0, 0, 0.27);
}
</style>
