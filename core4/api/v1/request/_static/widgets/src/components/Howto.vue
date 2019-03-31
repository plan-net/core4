<template>
  <div :class="type">
    <h2 class="title mb-3 pt-2">
      CORE4 widgets
    </h2>
    <p>
      In
      <em>CORE4</em> there are
      <span >widgets</span> and
      <span >boards</span>.
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
/* @keyframes blink {
  0% {
    border-color: #fae2e3;
  }
  50% {
    border-color: #be0406;
  }
  100% {
    border-color: #fae2e3;
  }
}

@keyframes blink2 {
  0% {
    border-color: #034d8c;
  }
  50% {
    border-color: #b6d8e9;
  }
  100% {
    border-color: #034d8c;
  }
}

@keyframes blink3 {
  0% {
    border-color: lighten(#64a505, 35);
  }
  50% {
    border-color: #64a505;
  }
  100% {
    border-color: lighten(#64a505, 35);
  }
}

.howto-helper {
  .widgets,
  .widget,
  .widget-list,
  .boards {
    position: relative;
    &:after {
      display: block;
      position: absolute;
      font-size: 16px;
      font-weight: 700;
      top: 18px;
      color: white;
      padding: 5px;
      border-radius: 3px;
      right: 5px;
      box-shadow: 0px 1px 3px 0px rgba(0, 0, 0, 0.2),
        0px 1px 1px 0px rgba(0, 0, 0, 0.14),
        0px 2px 1px -1px rgba(0, 0, 0, 0.12);
    }
  }
  .widget-list {
    > div > div {
      border: 2px dashed #0a7db4;
      animation: blink2 3s infinite;
      &:after {
        content: "WIDGET";
        padding: 2px;
        z-index: 10000;
        background-color: #0a7db4;
        color: #fff;
      }
    }
  }
  .boards {
    .list__tile {
      border: 2px dashed #d70f14;
      animation: blink 3s infinite;
    }

    &:after {
      content: "BOARDS";
      right: 130px;
      background-color: #d70f14;
    }
  }
  .widget {
    border: 2px dashed #64a505;
    animation: blink3 3s infinite;
    &:after {
      content: "NORMAL VIEW";
      background-color: #64a505;
    }
  }
} */
</style>
<style scoped lang="scss">
div.standalone {
  max-width: 760px;
}
</style>
