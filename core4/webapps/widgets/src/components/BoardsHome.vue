<template>
  <div>
    <board v-if="ready" />
    <widget-manager></widget-manager>
    <create-dialog
      v-model="nameDialog"
      :board="activeBoard"
    ></create-dialog>
  </div>
</template>

<script>
import WidgetManager from '@/components/WidgetManager'
import Board from '@/components/Board'
import CreateDialog from '@/components/CreateDialog'
export default {
  name: 'boards-home',
  components: {
    WidgetManager,
    CreateDialog,
    Board
  },
  methods: {
    onEditBoardName (isNew = false) {
      if (isNew === false) {
        this.activeBoard = this.$store.getters.activeBoard
      }
      this.nameDialog = true
    }
  },
  mounted () {
    this.$bus.$on('edit-board-name', this.onEditBoardName)
  },
  data () {
    return {
      activeBoard: null,
      nameDialog: false
    }
  },
  watch: {
    nameDialog (val) {
      if (val === false) {
        this.activeBoard = null
      }
    }
  },
  computed: {
    ready () {
      return this.$store.getters.ready
    }
  }
}
</script>

<style scoped lang="scss">
</style>
