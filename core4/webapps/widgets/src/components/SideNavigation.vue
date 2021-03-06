<template>
  <v-container
    fluid
    class="boards-container"
  >
    <v-row
      column
      no-gutters
    >

      <v-col
        cols="12"
        class=" px-3"
      >
        <v-divider></v-divider>
      </v-col>
      <v-col
        cols="12"
        class="mt-4"
      >
        <v-list>
          <v-subheader
            v-ripple
            @click="boardsVisible = !boardsVisible"
          >
            MY BOARDS <span
              class="ml-2"
              v-if="!boardsVisible"
            >({{boards.length}})</span>
            <v-spacer></v-spacer>
            <v-icon
              small
              v-if="boardsVisible"
            >mdi-menu-up</v-icon>
            <v-icon
              small
              v-else
            >mdi-menu-down</v-icon>
          </v-subheader>
          <div class="boards-group">
            <v-list-item-group
              class="sub-boards-group"
              v-if="boardsVisible"
              color="primary"
            >
              <template v-if="boards != null">
                <template v-for="brd in boards">
                  <v-list-item
                    class="pr-0"
                    :mouse-over="brd.over=true"
                    :mouse-out="brd.over=false"
                    :key="brd.name"
                    @click="setActiveBoard(brd.name)"
                  >
                    <v-list-item-icon>
                      <v-icon>mdi-view-dashboard-variant</v-icon>
                    </v-list-item-icon>
                    <v-list-item-content>
                      <v-list-item-title>
                        {{brd.name}}
                      </v-list-item-title>
                    </v-list-item-content>
                    <v-list-item-action>
                      <v-icon
                        @click="onEditBoard(brd.name)"
                        ripple
                        small
                        color="grey"
                      >mdi-pencil</v-icon>
                    </v-list-item-action>
                  </v-list-item>
                </template>
              </template>
              <template v-else>
                <v-boilerplate
                  v-for="i in 2"
                  :key="i"
                  class="pt-3"
                  :loading="boards == null"
                  type="list-item-avatar"
                ></v-boilerplate>
              </template>
            </v-list-item-group>
          </div>
          <v-list-item-group v-model="selected">
            <v-list-item @click.stop.prevent="dialogOpen = true">
              <v-list-item-icon>
                <v-icon>mdi-plus-circle</v-icon>
              </v-list-item-icon>
              <v-list-item-content>
                <v-list-item-title>
                  Add board
                </v-list-item-title>
              </v-list-item-content>
            </v-list-item>
          </v-list-item-group>
        </v-list>
      </v-col>
    </v-row>
    <v-dialog
      v-model="dialogOpen"
      width="500"
    >
      <v-card>
        <v-card-title>
          <!-- start -->
          <v-row no-gutters>
            <h2 class="text-h4">{{oldName ? 'Change name' : 'Add board'}}</h2>
            <v-spacer></v-spacer>
            <v-btn
              icon
              @click="dialogOpen = false"
            >
              <v-icon>mdi-close</v-icon>
            </v-btn>
          </v-row>
          <!-- end -->
        </v-card-title>
        <ValidationObserver
          ref="observer"
          v-slot="{ handleSubmit }"
        >
          <!--  validated,, validate, invalid,  -->
          <ValidationProvider
            name="Boardname"
            :rules="{required: true,max: 30, boardexists: error}"
            v-slot="{ errors }"
          >
            <v-form @submit.prevent="handleSubmit(submit)">
              <!-- , valid -->
              <v-card-text class="pt-5 pb-0">
                <v-text-field
                  autofocus
                  clearable
                  outlined
                  filled
                  v-model="name"
                  :error-messages="errors"
                  label="Boardname"
                  required
                ></v-text-field>
              </v-card-text>
              <v-card-actions class="pt-4 pb-8 px-7">
                <v-btn
                  color="primary"
                  text
                  :disabled="boards.length <= 1"
                  @click="deleteBoard"
                >
                  Delete board
                </v-btn>
                <v-spacer></v-spacer>
                <v-btn
                  color="primary"
                  text
                  @click="dialogOpen = false; oldName = null; name = null"
                >
                  Cancel
                </v-btn>
                <v-btn
                  :disabled="block"
                  color="primary"
                  type="submit"
                >
                  Save
                </v-btn>
              </v-card-actions>
            </v-form>
          </ValidationProvider>
        </ValidationObserver>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script>
import { mapGetters, mapActions } from 'vuex'
import { ValidationProvider, ValidationObserver } from 'vee-validate'
import _ from 'lodash'
export default {
  mounted () {
    window.addEventListener('resize', _.debounce(this.update, 250))
  },
  components: {
    ValidationProvider,
    ValidationObserver,
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
  computed: {
    ...mapGetters('widgets', [
      'boards', 'board'
    ])
  },
  data () {
    return {
      selected: null,
      dialogOpen: false,
      block: false,
      boardsVisible: true,
      name: null,
      oldName: null,
      error: null
    }
  },
  watch: {
    dialogOpen (newValue, oldValue) {
      if (newValue === false) {
        this.selected = []
        this.clear()
      }
    },
    name (newValue, oldValue) {
      if (this.error != null && newValue !== oldValue) {
        this.error = null
        this.block = false
        requestAnimationFrame(() => {
          this.$refs.observer.reset()
        })
      }
    }
  },
  methods: {
    ...mapActions('widgets', {
      setActiveBoard: 'setActiveBoard',
      delBoard: 'deleteBoard'
    }),
    async update () {
      await this.$nextTick()

      const logoCnt = document.querySelector('.c4-navigation-logo-container')
      const logoCntHeight = logoCnt.offsetHeight

      const footerCnt = document.querySelector('.c4-navigation-footer')
      const footerCntHeight = footerCnt.offsetHeight

      const snav = document.querySelector('.c4-navigation')
      const snavHeight = snav.offsetHeight

      const targetHeight = snavHeight - footerCntHeight - logoCntHeight

      /*       console.log(elem.offsetHeight)
      console.log(logoCntHeight, footerCntHeight)
      console.log(snavHeight) */
      /// ///////////////
      this.$el.style.height = `${targetHeight}px`
      const boardsGroupHeight = (targetHeight - 56 - 100)
      const subHeight = this.$el.querySelector('.sub-boards-group').offsetHeight
      console.log(boardsGroupHeight, subHeight)
      const el = this.$el.querySelector('.boards-group')
      if (subHeight >= boardsGroupHeight) {
        el.style.height = boardsGroupHeight + 'px'
        el.classList.add('shadow')
      } else {
        el.style.height = 'auto'
        el.classList.remove('shadow')
      }
      // this.$el.querySelector('.boards-group').style.height = (targetHeight - 56 - 100) + 'px'
    },
    deleteBoard (name) {
      this.delBoard(this.name)
      this.dialogOpen = false
      this.oldName = null
      this.name = null
    },
    onEditBoard (name) {
      this.oldName = name
      this.name = name
      this.dialogOpen = true
    },
    async clear () {
      this.oldName = null
      this.block = false
      this.name = null
      this.dialogOpen = false
      requestAnimationFrame(() => {
        this.$refs.observer.reset()
      })
      this.error = null
    },
    async submit () {
      await this.$nextTick()
      this.$refs.observer.validate().then(async isValid => {
        console.log(isValid)
        if (isValid) {
          this.block = true
          try {
            const action = this.oldName != null ? 'widgets/editBoard' : 'widgets/createBoard'
            const dto = { board: this.name, oldName: this.oldName }
            await this.$store.dispatch(action, dto)
            const text = this.oldName != null ? `Board „${this.name}“ changed.` : `Board „${this.name}“ created.`
            this.$bus.$emit('SHOW_NOTIFICATION', {
              type: 'success',
              text
            })
            this.clear()
          } catch (err) {
            console.log(err, 'error caught')
            if (err.message === 'Board exists') {
              this.error = err.message + '.'
            }
          }
        }
      })
    }
  }
}
</script>

<style lang="scss" scoped>
.boards-group {
  &.shadow {
    box-shadow: inset -5px -7px 28px -16px #666;
  }
}
img.client {
  width: 90%;
  height: auto;
  margin: 0 auto;
  display: block;
}
::v-deep .v-skeleton-loader__list-item-avatar {
  padding-left: 9px;
}
.boards-group {
  overflow-x: auto;
}
</style>
