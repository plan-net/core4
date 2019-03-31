<template>
  <v-card class="pnbi-card pb-2">
    <v-toolbar
      flat

      class="pnbi-datatable__toolbar pb-0 pt-2"
    >
      <h3 class="card-headline">{{label}}</h3>
      <v-spacer></v-spacer>
      <!-- @slot Use this slot for buttons that control important parts of the card  (optional)-->
      <slot name="primary-controls">
      </slot>
    </v-toolbar>
    <v-card-text class="px-4 py-2">
      <!-- @slot Main Slot. Use this slot to place the card content -->
      <slot></slot>
    </v-card-text>
    <template v-if="!!$slots['card-actions']">
      <v-card-actions class="px-3 pt-2">
        <v-spacer></v-spacer>
        <!-- @slot Use this slot card actions (optional) -->
        <slot name="card-actions"></slot>
      </v-card-actions>
    </template>
  </v-card>
</template>

<script>
import ContentContainerMixin from '../../internal/ContentContainerMixin'

export default {
  name: 'pnbi-card',
  mixins: [ContentContainerMixin]
}
</script>

<style scoped lang="scss">
.theme--dark{
  .card-headline{
    color: #fff;
  }
}
.theme--light{
  .card-headline{
    color: var(--v-accent-base);
  }

}
</style>
