<template>
  <v-layout class="circle-container pl-1">
    <v-icon>more_vert</v-icon>
    <v-icon>more_vert</v-icon>
    <v-icon>more_vert</v-icon>
  </v-layout>
</template>

<style scoped>
  div.circle-container{
    width: 26px;
    height: 24px;
    overflow: hidden;
  }
  div >>> .v-icon{
    width: 9px;
    font-size: 34px;
    font-weight: bold;
    /* color: var(--v-secondary-lighten5) !important; */
/*     font-weight: bold;
    margin-left: -.34rem;
    margin-top: -.1rem;
    font-size: 34px !important; */
  }
</style>
