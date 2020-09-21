<template>
  <div>
    <v-dialog
      v-model="dialogOpen"
      width="1090px"
      scrollable
    >
      <template v-slot:activator="{ on, attrs }">
        <v-btn
          color="primary"
          dark
          v-bind="attrs"
          v-on="on"
        >
          <v-icon left>mdi-plus-circle</v-icon>
          Add widgets to „{{board}}“
        </v-btn>
      </template>

      <v-card>
        <v-card-title>
          <!-- start -->
          <v-row no-gutters>
            <h2 class="text-h4">Add widgets to „{{board}}“</h2>
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
        <v-divider class="mx-6"></v-divider>
        <v-row
          align="center"
          class="pl-7 pr-6"
        >
          <tag-leiste
            class="py-2"
            :selected="selectedTag"
            @change="selectedTag=$event"
          ></tag-leiste>

          <v-row
            no-gutters
            class="search-component pr-4"
          >
            <template>
              <v-row class="pl-9">
                <search
                  class="pl-3"
                  :search-active="true"
                  @close-input="()=>{}"
                ></search>
              </v-row>
            </template>
            <!--             <template v-else>
              <v-spacer></v-spacer>
              <v-btn
                icon
                @click="searchActive = true"
              >
                <v-icon>mdi-magnify</v-icon>
              </v-btn>
            </template> -->
          </v-row>
        </v-row>

        <v-card-text class="pt-3 widgetsearch-card-text">
          <v-row>
            <small-widget
              v-for="(widget, $index) in widgets"
              :key="$index"
              :widget="widget"
              @change="onChange"
            ></small-widget>
          </v-row>
          <infinite-loading @infinite="searchWidgets" />
        </v-card-text>

        <v-card-actions class="pt-4 pb-4 px-7">
          <v-spacer></v-spacer>
          <v-btn
            color="primary"
            text
            @click="this.deltaWidgets = [];
            dialogOpen = false"
          >
            Cancel
          </v-btn>
          <v-btn
            color="primary"
            @click="dialogOpen = false"
          >
            Save
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
// import { mapState, mapActions } from 'vuex'
import api from '@/store/api.js'
import TagLeiste from '@/components/sub/TagLeiste'
import SearchField from '@/components/sub/SearchField'
import SmallWidget from '@/components/sub/SmallWidget'
import InfiniteLoading from 'vue-infinite-loading'
import { mapState } from 'vuex'
export default {
  components: {
    TagLeiste,
    search: SearchField,
    InfiniteLoading,
    SmallWidget

  },
  computed: {
    ...mapState('widgets', [
      'board'
    ])
  },
  data () {
    return {
      deltaWidgets: [],
      selectedTag: 'all',
      dialogOpen: true,
      // searchActive: false,
      params: {
        search: '',
        page: 0,
        per_page: 4
      },
      widgets: []
    }
  },
  methods: {
    onChange (payload) {
      const w = payload.widget
      const added = payload.added
      if (payload.isNew === false) {
        // already in the board
        // we listen to changes  - if user wants to remove or add
        // added may be true|false
        this.deltaWidgets = this.deltaWidgets.filter(val => val.rsc_id === w.rsc_id)
        if (added === false) {
          this.deltaWidgets.push(w)
        }
      } else {
        if (added === true) {
          this.deltaWidgets.push(w)
        } else {
          this.deltaWidgets = this.deltaWidgets.filter(val => val.rsc_id === w.rsc_id)
        }
      }
    },
    async updateBoard () {
      await this.$store.dispatch('widgets/updateBoard', this.deltaWidgets)
    },
    onDialogOpen () {
      // this.searchWidgets()
    },
    async searchWidgets ($state = {
      loaded: () => {},
      complete: () => {}
    }) {
      const ret = await api.searchWidgets(this.params)
      if (ret.data.length) {
        this.params.page += 1
        this.widgets.push(...ret.data)
        // await this.$nextTick()
        $state.loaded()
      } else {
        $state.complete()
      }
    }
    /*    ...mapActions('widgets', {
      searchWidgets: 'searchWidgets'
    }) */
  },
  mounted () {
    // this.searchWidgets()
  },
  watch: {
    dialogOpen (newValue, oldValue) {
      // this.onDialogOpen()
      if (newValue === false) {
        this.updateBoard()
        // this.deltaWidgets = []
      } else {

      }
    }
  }

}
</script>

<style lang="scss" scoped>
::v-deep .widgetsearch-card-text.v-card__text {
  background-color: #fcfcfd;
  height: 520px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.15);
  border-top: 1px solid rgba(0, 0, 0, 0.15);
}
</style>
