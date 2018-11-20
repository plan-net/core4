<template>
   <v-container fluid>
      <v-card>
        dlkfhjksdhf
      </v-card>
    </v-container>
</template>
<script>
import Api from '@/api/api'

export default {
  name: 'home',
  mounted () {
    Api.register().then(val => {
      console.log(val)
    })
  },
  components: {
  }
}
</script>
