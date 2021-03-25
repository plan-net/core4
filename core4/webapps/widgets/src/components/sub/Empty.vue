<template>
  <v-container fluid>
    <v-row
      align="center"
      justify="center"
    >
      <v-col
        cols="12"
        align="center"
      >
        <v-icon
          class="blob"
          style="font-size:5rem"
          x-large
          color="grey"
        >
          mdi-shape-square-plus
        </v-icon>
      </v-col>
      <v-col
        cols="12"
        align="center"
      >
        <h2 class="text-h4 mb-4">
          Add your first app
        </h2>
        <p class="text-h5" style="max-width: 480px;">
          You can organize apps into boards and quickly access them in the future.
        </p>
        <p class="body-1" style="max-width: 480px;">
          Click on the „Add apps to …“ button to add apps to this board.
        </p>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
export default {

}
</script>

<style lang="scss" scoped>
.blob {
  animation: pulse 5s infinite;
}

@keyframes pulse {
  0% {
    transform: scale(0.7);
  }

  62% {
     transform: scale(1.0);
  }

  100% {
     transform: scale(0.7);
  }
}
</style>
