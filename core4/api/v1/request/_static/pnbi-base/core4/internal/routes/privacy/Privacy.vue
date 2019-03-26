<template>
  <pnbi-page header-type="2" small>
    <pnbi-card headline="Privacy Policy">
      <v-flex d-flex xs12>
        -
      </v-flex>
    </pnbi-card>
  </pnbi-page>
</template>

<script>

export default {
  props: {
    type: String
  },
  methods: {
    onClick () {
      if (this.type === 'dialog') {
        this.$emit('imprint-click')
      } else {
        this.$router.push('imprint')
      }
    }
  }
}

</script>
<style lang="scss" scoped>
.link {
  text-decoration: underline;
  cursor: pointer;
  color: var(--v-primary-base);
}
.v-card__text {
  padding-left: 0;
}
</style>
