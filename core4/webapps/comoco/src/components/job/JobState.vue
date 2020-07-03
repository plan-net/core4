<template>
  <v-row
    class="flags"
    justify="end"
    no-gutters
  >
    <v-tooltip bottom>
      <template v-slot:activator="{ on }">
        <span
          v-on="on"
          v-for="(icon, flag) in flags"
          class="text-uppercase font-weight-bold flag"
          :key="flag"
          :class="[ (job[flag]) ? 'active' : 'passive']"
        >
          {{ icon }}
        </span>
      </template>
      <span>K - killed, N - nonstop, R - removed, Z - zombie</span>
    </v-tooltip>
  </v-row>
</template>

<script>
export default {
  props: {
    flags: {
      type: Object,
      required: false
    },
    job: {
      type: Object,
      required: true
    }
  }
}
</script>

<style lang="scss" scoped>
.flags {
  margin-top: -2px;
  margin-bottom: 2px;
  font-size: 11.5px;
  padding-right: 3px;
  .flag {
    margin-left: 1px;
  }
}
</style>
