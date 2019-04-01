<script>
export default {
/*   props: {
    state: String
  } */
}
</script>
<template>
  <v-container fill-height>
    <v-layout align-center>
      <v-flex class="text-center">
        <v-form ref="form" lazy-validation>
          <v-card class="pb-4">
            <v-card-title class="justify-center pb-0">
              <h1 class="bi-headline">Cookies</h1>
            </v-card-title>
            <v-card-text class="">
              <p class="ma-0">Wir verwenden
                <strong>Cookies</strong>, um die Aufrufe unserer Website zu analysieren. Mit der Nutzung unserer Website erklären Sie sich damit einverstanden.
              </p>
            </v-card-text>
            <v-card-actions class="white pt-0">
              <v-layout column>
                <v-flex class="mb-3">
                  <v-btn flat block @click.stop="$emit('open-privacy-dialog')" color="primary">Mehr Informationen</v-btn>
                </v-flex>
                <v-flex>
                  <v-btn block color="primary" type="submit" @click.prevent="$emit('privacy-ok-clicked')">Zustimmen</v-btn>
                </v-flex>
              </v-layout>
            </v-card-actions>
          </v-card>
        </v-form>
      </v-flex>
    </v-layout>
  </v-container>

</template>
<style scoped lang="scss">
</style>
