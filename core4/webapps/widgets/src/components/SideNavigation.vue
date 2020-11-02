<template>
  <v-container fluid>
    <v-row
      column
      no-gutters
    >
     <!--  <v-col
        class="mt-16 pt-8"
        cols="12"
      >
        <img
          class="client"
          src="img/targobank-logo.svg"
          alt=""
        >
      </v-col> -->
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
          <v-list-item-group
            v-if="boardsVisible"
            color="primary"
          >
            <template v-if="boards != null">
              <template v-for="brd in boards">
                <v-list-item
                  class="pr-0"
                  :mouse-over="brd.over=true"
                  :mouse-out="brd.over=false"
                  xxxdisabled="(brd.name === board)"
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

export default {
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
    }
  },
  methods: {
    ...mapActions('widgets', {
      setActiveBoard: 'setActiveBoard'
    }),
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
    },
    async submit () {
      this.$refs.observer.validate().then(async isValid => {
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
          } catch (err) {
            if (err.message === 'Board exists') {
              this.error = err.message + '.'
            }
          } finally {
            this.clear()
          }
        }
      })
    }
  }
}
</script>

<style lang="scss" scoped>
img.client {
  width: 90%;
  height: auto;
  margin: 0 auto;
  display: block;
}
::v-deep .v-skeleton-loader__list-item-avatar {
  padding-left: 9px;
}
</style>
