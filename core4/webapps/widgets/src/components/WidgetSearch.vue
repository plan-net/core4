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
          Add apps to „{{board}}“
        </v-btn>
      </template>

      <v-card>
        <v-card-title>
          <!-- start -->
          <v-row no-gutters>
            <h2 class="text-h4">Add apps to „{{board}}“</h2>
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
            @change="onTagSelection"
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
                  @close-input="onUserSearch"
                ></search>
              </v-row>
            </template>

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
          <infinite-loading
            ref="il"
            @infinite="searchWidgets"
          />
        </v-card-text>

        <v-card-actions class="pt-4 pb-4 px-7">
          <v-chip
            class="ma-2"
            color="grey"
            xxxlabel
            text-color="white"
          >
            <v-avatar
              left
              class="grey darken-2"
            >
              {{total}}
            </v-avatar>
            {{total !== 1 ? 'Widgets':'Widget'}} found
          </v-chip>
          <v-spacer></v-spacer>
          <v-btn
            color="primary"
            text
            @click="deltaWidgets = [];
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
import api from '@/store/api.js'
import TagLeiste from '@/components/sub/TagLeiste'
import SearchField from '@/components/sub/SearchField'
import SmallWidget from '@/components/sub/SmallWidget'
import InfiniteLoading from 'vue-infinite-loading'
import { mapState, mapActions } from 'vuex'
import _ from 'lodash'

const defParams = {
  search: '',
  page: 0,
  per_page: 6
}
export default {
  components: {
    TagLeiste,
    search: SearchField,
    InfiniteLoading,
    SmallWidget

  },
  computed: {
    ...mapState('widgets', [
      'board', 'tags'
    ]),
    params2 () {
      const filter = { tag: { $in: [this.selectedTag] } }
      return Object.assign(this.params, { filter })
    }
  },
  data () {
    const params = _.cloneDeep(defParams)
    return {
      deltaWidgets: [],
      selectedTag: 'all',
      dialogOpen: false,
      total: 0,
      params,
      widgets: []
    }
  },
  methods: {
    async onUserSearch (val) {
      const search = val ? val.text : this.params.search
      this.params = Object.assign(_.cloneDeep(defParams), { search })
      this.widgets = []
      this.deltaWidgets = []
      // this.selectedTag = 'all'
      await this.$nextTick()
      this.$refs.il.stateChanger.reset()
      // this.searchWidgets()
    },
    onTagSelection ($event) {
      this.selectedTag = $event
      this.onUserSearch()
    },
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
      if (this.deltaWidgets.length) {
        await this.$store.dispatch('widgets/updateBoard', this.deltaWidgets)
        this.deltaWidgets = []
      }
    },
    onDialogOpen () {
      // this.searchWidgets()
    },
    async searchWidgets ($state = {
      loaded: () => {},
      complete: () => {}
    }) {
      try {
        const ret = await api.searchWidgets(this.params)
        this.total = ret.total_count
        if (ret.data.length) {
          this.params.page += 1
          this.widgets.push(...ret.data)
          $state.loaded()
        } else {
          $state.complete()
        }
      } catch (err) {
        $state.error()
      }
    },
    ...mapActions('widgets', {
      fetchTags: 'fetchTags'
    })
  },
  mounted () {
    // this.searchWidgets()
  },
  watch: {
    dialogOpen (newValue, oldValue) {
      if (newValue === false) {
        this.updateBoard()
      } else {
        if (this.tags.length === 0) {
          this.fetchTags()
        }
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
