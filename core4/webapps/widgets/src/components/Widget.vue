<template>
  <div
    class="widget"
    :style="style"
  >
    <div class="widget-content">
      <!-- Safe zone, enter your custom markup -->
      <v-card class="c4-card mx-auto rounded-lg elevation-3 flex-column d-flex">
        <template v-if="widget.error != null">
          <widget-error :widget="widget"></widget-error>
        </template>
        <template v-else-if="isHtml">
          <v-boilerplate
            class="pt-12"
            v-if="loading"
            :loading="loading"
            type="avatar, article"
          ></v-boilerplate>
          <v-card-text
            class="pb-5"
            v-show="!loading"
          >
            <iframe scrolling="no"
              src="about:blank"
              frameborder="0"
              id="frame"
            >
            </iframe>
          </v-card-text>
        </template>
        <template v-else>
          <v-card-title class="flex-column pt-10 pb-8">
            <v-avatar
              color="accent"
              size="80"
              class="c4-avatar mx-auto mb-3"
            >
              <v-icon
                dark
                large
              >{{widget.icon}}</v-icon>
            </v-avatar>
            <div class="c4-card--widget-title grey--text text--darken-1 mx-auto body-1">{{widget.title}} </div>

          </v-card-title>
          <v-card-text class="pb-2">
            <div class="subtitle-2 mb-1 text-truncate">{{widget.subtitle}}</div>
            <div
              class="body-2 font-weight-light desc"
              v-html="widget.description_html"
            ></div>
          </v-card-text>
        </template>
        <v-card-actions ripple>
          <v-btn
            v-if="widget.error == null"
            color="primary"
            text
            @click="open"
          >Open App</v-btn>
          <v-btn
            v-else
            color="primary"
            text
            @click="fixMissingWidget"
          >Fix App</v-btn>
          <v-spacer></v-spacer>
          <v-menu
            bottom
            offset-y
            open-on-hover
          >
            <template v-slot:activator="{ on, attrs }">
              <v-btn
                icon
                v-bind="attrs"
                v-on="on"
              >
                <v-icon>mdi-dots-vertical</v-icon>
              </v-btn>
            </template>
            <v-list class="c4-menu-list">
              <v-list-item @click="onHelpClick">
                <v-list-item-icon class="mr-4">
                  <v-icon>mdi-help-circle</v-icon>
                </v-list-item-icon>
                <v-list-item-content>
                  <v-list-item-title>Help</v-list-item-title>
                </v-list-item-content>
              </v-list-item>
              <v-list-item disabled>
                <v-list-item-icon class="mr-4">
                  <v-icon>mdi-share-variant</v-icon>
                </v-list-item-icon>
                <v-list-item-content>
                  <v-list-item-title>Share</v-list-item-title>
                </v-list-item-content>
              </v-list-item>
              <v-list-item @click="onRemove">
                <v-list-item-icon class="mr-4">
                  <v-icon>mdi-delete</v-icon>
                </v-list-item-icon>
                <v-list-item-content>
                  <v-list-item-title>Remove</v-list-item-title>
                </v-list-item-content>
              </v-list-item>
            </v-list>
          </v-menu>
        </v-card-actions>
        <v-tooltip bottom>
          <template v-slot:activator="{ on, attrs }">
            <v-btn
              v-if="showHandle"
              v-bind="attrs"
              v-on="on"
              class="handle text--disabled"
              small
              icon
            >
              <!-- <v-icon>mdi-drag-variant</v-icon> -->
              <v-icon>mdi-drag</v-icon>
            </v-btn>
          </template>
          <span>Drag &amp; sort apps</span>
        </v-tooltip>
      </v-card>
      <!-- Safe zone ends -->
    </div>

  </div>
</template>

<script>
// git import _ from 'lodash'
import { mapActions } from 'vuex'
// import { config } from '@/main'
import { replacePort } from '@/plugins/fixme.js'
import WidgetError from '@/components/sub/WidgetError'
const baseWidth = 320
const baseHeight = 360
const margin = 15
export default {
  inject: ['theme'],
  async mounted () {
    await this.$nextTick()
    if (this.html != null && this.html.length > 2) {
      // this.setupHTMLDebounce(this.setupHTML, 333)
      // this.setupHTML()
    } else {
      if (this.widget.custom_card === false) {
        this.loading = false
      }
    }
  },
  data () {
    return {
      loading: true
    }
  },

  methods: {
    onMessage (e) {
      const iframeEl = this.$el.querySelector('iframe').contentWindow
      if (e.source === iframeEl) {
        if (e.data.event === 'WidgetLoaded') {
          window.setTimeout(() => {
            this.loading = false
          }, 500)
        } else if (e.data.event === 'WidgetOpen') {
          this.open({
            payload: e.data.payload || ''
          })
        }
      }
    },
    async fixMissingWidget () {
      await this.$store.dispatch('widgets/fixWidget', this.widget)
    },
    /*     setupHTMLDebounce (func, delay) {
      console.log(func)
      let debounceTimer
      return function () {
        console.log('debouncing call..')
        const context = this
        const args = arguments
        clearTimeout(debounceTimer)
        debounceTimer = setTimeout(() => func.apply(context, args), delay)
        console.log('..done')
      }
    },
    setupHTMLDebounce2: _.debounce(function () {
      this.setupHTML()
    }, 333), */
    setupHTML () {
      if (this.widget.html == null) {
        return
      }
      const iframeEl = this.$el.querySelector('iframe').contentWindow
      window.addEventListener('message', this.onMessage, false)
      const doc = iframeEl.document
      doc.open()
      const tmp = this.widget.html.split('</head>')

      const t = this.$vuetify.theme.themes
      // eslint-disable-next-line
      const vars = `<script>window.__DARK__=${JSON.stringify(this.dark)}; window.__THEME__=${JSON.stringify(t)}<\/script></head>`
      const res = tmp[0] + vars + tmp[1]
      doc.write(res)
      doc.close()
      // this.loading = false
    },
    ...mapActions('widgets', {
      removeFromBoard: 'removeFromBoard'
    }),
    onRemove () {
      this.removeFromBoard(this.widget.rsc_id)
    },
    onHelpClick () {
      const endpoint = replacePort(this.widget.endpoint[0])
      const params = { widgetId: this.widget.rsc_id, endpoint }
      this.$router.push({ name: 'help', params })
    },
    open (dto) {
      if (this.widget.target === 'blank') {
        window.open(this.widget.enter_url || this.widget.endpoint.enter_url, '_blank')
      } else {
        const endpoint = replacePort(this.widget.endpoint[0])
        const params = { widgetId: this.widget.rsc_id, endpoint, payload: dto.payload }
        this.$router.push({ name: 'enter', params })
      }
    }
  },
  components: {
    WidgetError,
    VBoilerplate: {
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
    }
  },
  props: {
    widget: {
      type: Object,
      default: () => {
        return {

        }
      },
      required: false
    },
    showHandle: {
      type: Boolean,
      default: true
    }
  },
  watch: {
    async html  (newValue, oldValue) {
      if (newValue) {
        this.setupHTML()
        // this.setupHTMLDebounce(this.setupHTML, 333)
      }
    }
  },
  beforeDestroy () {
    // window.removeEventListener('message', this.onMessage)
  },
  computed: {
    isHtml () {
      return this.widget.custom_card === true
    },
    html () {
      return this.widget.html
    },
    h () {
      const h = Number((this.widget.res || 11).toString().split('')[1])
      let temp = h * baseHeight
      if (h === 2) {
        temp += margin * 2
      }
      return (temp).toString() + 'px'
    },
    w () {
      const w = Number((this.widget.res || 11).toString().split('')[0])
      let temp = w * baseWidth
      if (w === 2) {
        temp += margin * 2
      }
      return (temp).toString() + 'px'
    },
    style () {
      return {
        height: this.h,
        width: this.w
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.desc {
  max-height: 86px;
  overflow-y: auto;
}
::v-deep .v-skeleton-loader {
  height: 100%;
}
::v-deep .v-skeleton-loader__avatar {
  width: 80px;
  height: 80px;
  margin-left: auto;
  margin-right: auto;
}
::v-deep .v-skeleton-loader__heading {
  margin-left: auto !important;
  margin-right: auto !important;
}
.widget {
  position: absolute;
  margin: 15px;
  z-index: 1;
  color: #fff;
  will-change: transform;
  .v-card {
    height: inherit;
    .v-card__text {
      width: inherit;
    }
  }
  .handle {
    opacity: 0.75;
    position: absolute;
    left: 5px;
    top: 5px;
    /*     right: 5px;
    bottom: 5px; */
  }
}
.c4-card .v-card__actions .v-btn--icon {
  padding: 0 0px;
}
.widget.muuri-item-dragging {
  z-index: 3;
}
.widget.muuri-item-releasing {
  z-index: 2;
}
.widget.muuri-item-hidden {
  z-index: 0;
}
.widget-content {
  height: 100%;

  iframe {
    overflow: hidden;
    width: 100%;
    height: 100%;
  }
}
</style>
