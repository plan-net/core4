<template>
  <v-app
    class="pnbi-webapp"
    :light="dark"
    :dark="dark"
  >
    <template v-if="isNavVisible">
      <pnbi-navigation>
        <slot name="navigation-slot"></slot>
      </pnbi-navigation>

      <transition name="slide">
        <v-toolbar
          flat
          clipped-left
          dense :dark="true"
          app class="pnbi-toolbar"
          fixed
        >
          <v-toolbar-side-icon @click="$bus.$emit('toggleSidenav')">
            <toolbar-side-icon/>
          </v-toolbar-side-icon>
          <!-- @slot Use this slot for a custom title instead of the default app-name -->
          <slot
            v-if="!!this.$slots['title-slot']"
            name="title-slot"
          ></slot>
          <h2
            v-else
            class="app-title"
          >{{title}}</h2>
          <v-spacer class="core-dotted"></v-spacer>
          <pnbi-user></pnbi-user>
        </v-toolbar>
      </transition>
      <v-content class="pt-0 core-background">
        <v-container
          :fluid="isFluid"
          class="core-container"
        >
          <!-- @slot Use this slot for router instance -->
          <slot name="router"></slot>
          <pnbi-snackbar></pnbi-snackbar>
        </v-container>
      </v-content>
    </template>
    <v-content
      v-else
      class="pa-0 ma-0 auth-routes"
    >
      <v-container
        fluid
        fill-height
        class="core-container"
      >
        <v-layout class="pa-0 ma-0">
          <v-flex class="pa-0 ma-0">
            <router-view />
          </v-flex>
        </v-layout>
      </v-container>
    </v-content>

    <v-progress-linear
      indeterminate
      v-if="loading"
    ></v-progress-linear>
    <error-dialog></error-dialog>
  </v-app>
</template>
<script>
/* import {
  TRACK,
  ERROR
} from '../../event-bus' */
import PnbiSnackbar from './pnbi-snackbar/Snackbar.vue'
import ErrorDialog from './pnbi-error-dialog/ErrorDialog.vue'
import Navigation from './pnbi-navigation/Navigation.vue'
import ToolbarSideIcon from './pnbi-navigation/pnbi-toolbar-side-icon.vue'
import PnbiUser from './pnbi-user/PnbiUser.vue'
import {
  mapActions,
  mapGetters
} from 'vuex'
export default {
  name: 'pnbi-webapp',
  props: {
    /**
     * Controls responsive behavior of the app.
     * If set to true the app content is full-width of the browser, even in large screen reslutions
    */
    fullWidth: {
      type: Boolean,
      default: false,
      required: false
    }
  },
  components: {
    PnbiSnackbar,
    ErrorDialog,
    PnbiUser,
    ToolbarSideIcon,
    'pnbi-navigation': Navigation
  },
  mounted () {
    this.fetchProfile()
    this.setUpEvents()
    this.$nextTick(() => {
      if (!this.fullWidth) {
        this._updateDimensions()
        window.addEventListener('resize', this._updateDimensions, { 'passive': true })
      }
    })
  },
  destroyed () {
    window.removeEventListener('resize', this._updateDimensions)
  },
  data () {
    return {
      alertMessage: null,
      alertOpen: false,
      clientWidth: 0
    }
  },
  methods: {
    ...mapActions([
      'fetchProfile',
      'logout',
      'setTitle'
    ]),
    setUpEvents () {
      /*       this.$bus.$on(TRACK, payload => {
        const dto = Object.assign({
          customer_id: this.profile._id,
          customer_email: this.profile.email,
          realname: this.profile.realname,
          webapp: this.title.toLowerCase()
        }, payload)
        if (payload.tealium_event === 'page_view') {
          window.utag.view(dto)
        } else {
          window.utag.link(dto)
        }
      }) */
    },
    _updateDimensions () {
      // TODO mixin
      this.clientWidth = Math.max(document.documentElement.clientWidth,
        window.innerWidth || 0)
    }
  },
  computed: {
    ...mapGetters([
      'profile',
      'loading',
      'title',
      'dark'
    ]),
    isNavVisible () {
      const meta = this.$route.meta || {
        hideNav: false
      }
      return !meta.hideNav
    },
    isFluid () {
      return (this.clientWidth < 1260) || (this.fullWidth)
    }
  }
}
</script>

<style lang="css">
.impressum {
  width: 22px;
  margin-top: -7px;
  text-align: center;
  font-weight: 700;
}

.v-navigation-drawer__border {
  opacity: 0.15;
}
</style>

<style scoped lang="css">
.slide-enter-active,
.slide-leave-active {
  top: 0;
}

.slide-enter,
.slide-leave-to {
  top: -48px;
}

.auth-routes >>> .container {
  padding: 0;
}

.auth-routes >>> .v-content__wrap {
  padding-top: 0;
}

pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  border: 1px solid rgba(100, 100, 100, 0.2);
}

.v-progress-linear {
  position: absolute;
  z-index: 10;
  top: -3px;
  margin: 0;
}

</style>
