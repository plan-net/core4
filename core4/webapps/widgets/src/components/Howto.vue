<template>
  <div :class="type">
    <h2 class="title mb-3 pt-2">
      CORE4 widgets
    </h2>
    <p>
      In
      <em>CORE4</em> there are
      <span>widgets</span> and
      <span>boards</span>.
      <br>
      <br> Widgets are small programs. These service or auxiliary programs can be, for example, a link list to access your BI
      applications, a summary of your company's main performance indicators and a gateway to access your raw data. They facilitate
      access to complex or simple functions.
      <br>
      <br> Widgets can have different states. A
      <span style="color: #64a505">normal view</span> and a maximum view that opens in fullscreen
      <!-- <v-icon color="primary">fullscreen</v-icon> -->when you click on the widget. The normal view often offers only a reduced number of functions or it is just a link
      to the maximum view of the widget.
      <br>
      <br> Boards contain any number of widgets and facilitate access to widgets. They can be compiled or deleted and can contain
      thematically related widgets.
    </p>
    <!--     <h3 class="title pb-2" style="margin-top: 0;">
      Next step
    </h3>
    <p>
      Click on <em class="primary--text" @click="showWidgetList()">TOGGLE WIDGETS</em> to open the widget overlay.<br>
      You can add widgets to the active board by clicking on the <span class="primary--text">(+)</span> next to the widget name.
    </p> -->
    <div class="text-xs-right">
      <!--       <v-btn flat color="primary" @click="showHelp()">Toggle help</v-btn>
      <v-btn flat color="primary" @click="showWidgetList()">Toggle widgets</v-btn> -->
      <slot name="button-slot"></slot>
    </div>
  </div>
</template>

<script>
export default {
  methods: {
    showWidgetList () {
      this.$bus.$emit('SHOW_WIDGETLIST')
    },
    showHelp () {
      const isToggled = document.querySelector('body').classList.contains('howto-helper')
      if (isToggled) {
        document.querySelector('body').classList.remove('howto-helper')
        this.$bus.$emit('SHOW_WIDGETLIST', false)
      } else {
        document.querySelector('body').classList.add('howto-helper')
        this.$bus.$emit('SHOW_WIDGETLIST', true)
      }
    }
  },
  beforeDestroy () {
    try {
      document.querySelector('body').classList.remove('howto-helper')
    } catch (err) {}
  },
  props: {
    type: {
      type: String,
      default: 'standalone'
    }
  }
}
</script>

<style lang="scss">
</style>
<style scoped lang="scss">
div.standalone {
  max-width: 760px;
}
</style>
