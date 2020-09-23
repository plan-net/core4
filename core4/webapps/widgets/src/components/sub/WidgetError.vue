<template>
  <div style="height: inherit;">
    <template>
      <v-card-title class="flex-column pt-10 pb-8">
        <v-avatar
          size="80"
          class="error darken-1 c4-avatar mx-auto mb-3 blob"
        >
          <v-icon
            dark
            x-large
          >mdi-alert-circle-outline</v-icon>
        </v-avatar>
        <div class="c4-card--widget-title grey--text text--darken-1 mx-auto body-1 error--text">{{widget.title}} </div>

      </v-card-title>
      <v-card-text class="pb-2">
        <div class="subtitle-2 mb-1 text-truncate error--text">{{widget.subtitle}}</div>
        <div
          class="body-2 error--text mb-3"
          v-html="widget.error"
        ></div>
        <p class="body-2 error--text">Something went wrong. Try to fix the error by clicking the fix button below.</p>
      </v-card-text>
    </template>
  </div>
</template>

<script>
export default {
  props: {
    widget: {
      required: true
    }
  },
  mounted () {
  },
  data () {
    return {
      loading: true
    }
  },
  components: {
    /*     VBoilerplate: {
      functional: true,
      render (h, { data, props, children }) {
        return h('v-skeleton-loader', {
          ...data,
          props: {
            boilerplate: true,
            elevation: 0,
            ...props
          }
        }, children)
      }
    } */
  }
}
</script>

<style lang="scss" scoped>
.v-card__text {
  width: inherit;
}
.blob {
  box-shadow: 0 0 0 0 rgba(255, 0, 0, 1);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(255, 0, 0, 0.7);
  }

  70% {
    box-shadow: 0 0 0 10px rgba(255, 0, 0, 0);
  }

  100% {
    box-shadow: 0 0 0 0 rgba(255, 0, 0, 0);
  }
}
</style>
