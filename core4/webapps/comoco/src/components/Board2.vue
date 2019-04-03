<template>
  <div id="#content">
    <grid-layout
      :responsive="true"
      :auto-size="false"
      :layout.sync="layout"
      :col-num="12"
      :row-height="240"
      :is-draggable="true"
      :is-resizable="false"
      :is-mirrored="false"
      :vertical-compact="false"
      :margin="[15, 15]"
      :use-css-transforms="true"
    >

      <grid-item :key="index"
        v-for="(item, index) in layout"
        :x="item.x"
        :y="item.y"
        :w="item.w"
        :h="item.h"
        :i="item.i"
      >
        {{item.i}}
      </grid-item>
    </grid-layout>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import VueGridLayout from 'vue-grid-layout'

export default {
  name: 'board',
  components: {
    GridLayout: VueGridLayout.GridLayout,
    GridItem: VueGridLayout.GridItem
  },
  mounted () {
    this.layout = [
      { 'x': 0, 'y': 0, 'w': 3, 'h': 1, 'i': '0' },
      { 'x': 3, 'y': 0, 'w': 3, 'h': 1, 'i': '1' }
    ]
  },
  computed: {
    ...mapGetters(['widgets'])
  },
  data () {
    return {
      layout: []
    }
  }
}
</script>

<style scoped>
/*** EXAMPLE ***/
#content {
    width: 100%;
}

.vue-grid-layout {
    xxxbackground: #eee;
    border: 1px solid rgba(255,255,255,.1);
}

.columns {
    columns: 120px;
}

.vue-resizable-handle {
    z-index: 5000;
    position: absolute;
    width: 20px;
    height: 20px;
    bottom: 0;
    right: 0;
    background: url('data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiBzdGFuZGFsb25lPSJubyI/Pg08IS0tIEdlbmVyYXRvcjogQWRvYmUgRmlyZXdvcmtzIENTNiwgRXhwb3J0IFNWRyBFeHRlbnNpb24gYnkgQWFyb24gQmVhbGwgKGh0dHA6Ly9maXJld29ya3MuYWJlYWxsLmNvbSkgLiBWZXJzaW9uOiAwLjYuMSAgLS0+DTwhRE9DVFlQRSBzdmcgUFVCTElDICItLy9XM0MvL0RURCBTVkcgMS4xLy9FTiIgImh0dHA6Ly93d3cudzMub3JnL0dyYXBoaWNzL1NWRy8xLjEvRFREL3N2ZzExLmR0ZCI+DTxzdmcgaWQ9IlVudGl0bGVkLVBhZ2UlMjAxIiB2aWV3Qm94PSIwIDAgNiA2IiBzdHlsZT0iYmFja2dyb3VuZC1jb2xvcjojZmZmZmZmMDAiIHZlcnNpb249IjEuMSINCXhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIgeG1sbnM6eGxpbms9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkveGxpbmsiIHhtbDpzcGFjZT0icHJlc2VydmUiDQl4PSIwcHgiIHk9IjBweCIgd2lkdGg9IjZweCIgaGVpZ2h0PSI2cHgiDT4NCTxnIG9wYWNpdHk9IjAuMzAyIj4NCQk8cGF0aCBkPSJNIDYgNiBMIDAgNiBMIDAgNC4yIEwgNCA0LjIgTCA0LjIgNC4yIEwgNC4yIDAgTCA2IDAgTCA2IDYgTCA2IDYgWiIgZmlsbD0iIzAwMDAwMCIvPg0JPC9nPg08L3N2Zz4=');
    background-position: bottom right;
    padding: 0 3px 3px 0;
    background-repeat: no-repeat;
    background-origin: content-box;
    box-sizing: border-box;
    cursor: se-resize;
}

.vue-grid-item:not(.vue-grid-placeholder) {
    background: #ccc;
    border: 1px solid black;
}

.vue-grid-item.resizing {
    opacity: 0.9;
}

.vue-grid-item.static {
    background: #cce;
}

.vue-grid-item .text {
    font-size: 24px;
    text-align: center;
    position: absolute;
    top: 0;
    bottom: 0;
    left: 0;
    right: 0;
    margin: auto;
    height: 100%;
    width: 100%;
}

.vue-grid-item .no-drag {
    height: 100%;
    width: 100%;
}

.vue-grid-item .minMax {
    font-size: 12px;
}

.vue-grid-item .add {
    cursor: pointer;
}

.vue-draggable-handle {
    position: absolute;
    width: 20px;
    height: 20px;
    top: 0;
    left: 0;
    background: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='10' height='10'><circle cx='5' cy='5' r='5' fill='#999999'/></svg>") no-repeat;
    background-position: bottom right;
    padding: 0 8px 8px 0;
    background-repeat: no-repeat;
    background-origin: content-box;
    box-sizing: border-box;
    cursor: pointer;
}
/* [
        { 'x': 0, 'y': 0, 'w': 2, 'h': 2, 'i': '0' },
        { 'x': 2, 'y': 0, 'w': 2, 'h': 4, 'i': '1' },
        { 'x': 4, 'y': 0, 'w': 2, 'h': 5, 'i': '2' },
        { 'x': 6, 'y': 0, 'w': 2, 'h': 3, 'i': '3' },
        { 'x': 8, 'y': 0, 'w': 2, 'h': 3, 'i': '4' },
        { 'x': 10, 'y': 0, 'w': 2, 'h': 3, 'i': '5' },
        { 'x': 0, 'y': 5, 'w': 2, 'h': 5, 'i': '6' },
        { 'x': 2, 'y': 5, 'w': 2, 'h': 5, 'i': '7' },
        { 'x': 4, 'y': 5, 'w': 2, 'h': 5, 'i': '8' },
        { 'x': 6, 'y': 3, 'w': 2, 'h': 4, 'i': '9' },
        { 'x': 8, 'y': 4, 'w': 2, 'h': 4, 'i': '10' },
        { 'x': 10, 'y': 4, 'w': 2, 'h': 4, 'i': '11' },
        { 'x': 0, 'y': 10, 'w': 2, 'h': 5, 'i': '12' },
        { 'x': 2, 'y': 10, 'w': 2, 'h': 5, 'i': '13' },
        { 'x': 4, 'y': 8, 'w': 2, 'h': 4, 'i': '14' },
        { 'x': 6, 'y': 8, 'w': 2, 'h': 4, 'i': '15' },
        { 'x': 8, 'y': 10, 'w': 2, 'h': 5, 'i': '16' },
        { 'x': 10, 'y': 4, 'w': 2, 'h': 2, 'i': '17' },
        { 'x': 0, 'y': 9, 'w': 2, 'h': 3, 'i': '18' },
        { 'x': 2, 'y': 6, 'w': 2, 'h': 2, 'i': '19' }
      ] */
</style>
