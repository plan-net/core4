<template>
  <v-dialog :scrollable="scrollable" lazy v-model="isOpen" :max-width="width">
    <v-card tile>
      <v-toolbar dense card dark color="accent">
        <v-toolbar-title class="ml-0">
          {{title}}
        </v-toolbar-title>
      </v-toolbar>
      <v-card-text class="px-3 py-3">
        <!-- @slot default dialog content -->
        <slot></slot>
        <!--<slot v-else name="dialog-content"></slot>-->
      </v-card-text>
      <v-card-actions class="pl-3 pr-3 py-3" style="background-color: rgba(100,100,100, .025)">
        <v-spacer></v-spacer>
        <!-- @slot default dialog actions -->
        <slot name="dialog-actions"></slot>
      </v-card-actions>
    </v-card>
  </v-dialog>

</template>

<script>
import DialogMixin from '../../internal/DialogMixin'

export default {
  name: 'pnbi-dialog',
  props: {
    /**
     * Sets dialog width
     */
    width: {
      type: [String, Number],
      default: '640px'
    },
    /**
     * Sets scrollable variable to true or false
     */
    scrollable: {
      type: Boolean,
      default: false
    },
    /**
     * Sets dialog headline
     */
    title: {
      type: String,
      required: true,
      default: ':title'
    }
  },
  mixins: [ DialogMixin ]
}
</script>
<style scoped>
</style>
