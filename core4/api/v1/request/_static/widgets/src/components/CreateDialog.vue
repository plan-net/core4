<template>
  <v-dialog
    v-model="open"
    persistent
    max-width="500px"
  >
    <v-card style="width: 100%;">
      <v-card-title>
        <span
          v-if="board && board.name"
          class="headline"
        >Change board name</span>
        <span
          v-else
          class="title"
        >Create board</span>
      </v-card-title>
      <v-card-text>
        <v-form ref="form">
          <v-container>
            <v-layout wrap>
              <v-flex xs12>
                <v-text-field
                  v-validate="'required|min:3|max:25|board_exists'"
                  :counter="25"
                  data-vv-name="Name"
                  :error-messages="errors.collect('Name')"
                  @keyup.enter.native="onSave"
                  autofocus
                  label="Name"
                  v-model="name"
                  required
                ></v-text-field>
              </v-flex>
            </v-layout>
          </v-container>
        </v-form>
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn
          color="primary"
          @click.native="onCancel"
        >Cancel</v-btn>
        <v-btn
          color="primary"
          :disabled="errors.any()"
          @click.native="onSave"
        >Save</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
import {
  mapActions
} from 'vuex'

export default {
  props: {
    value: {
      type: Boolean,
      required: true,
      default: false
    },
    board: {
      type: Object,
      required: false
    }
  },
  created () {
    this.$validator.extend('board_exists', {
      getMessage: field => `The board already exists.`,
      validate: value => {
        if (this.internalBoards.length === 0) {
          return true
        }
        const notExists = this.internalBoards.find(val => ((val.name != null) && val.name.toLowerCase() === value.toLowerCase())) ==
            null
        return notExists
      }
    })
  },
  mounted () {
    if (this.board != null) {
      this.name = this.board.name
    }
  },
  watch: {
    open (newValue, oldValue) {
      if (this.board != null) {
        this.name = this.board.name
      } else {
        this.name = null
      }
    }
  },
  computed: {
    open () {
      return this.value
    },
    internalBoards: {
      get: function () {
        const boards = this.$store.getters.boardsSet
        if (this.board != null) {
          // if board exists
          return boards.filter(val => val.name !== this.board.name)
        }
        return boards
      },
      set: function (newValue) {}
    }
  },
  data () {
    return {
      name: null
    }
  },
  methods: {
    ...mapActions(['createBoard', 'updateBoard']),

    onSave () {
      this.$validator.validateAll().then(valid => {
        if (valid) {
          if (this.board != null) {
            this.updateBoard(this.name)
          } else {
            this.createBoard({
              name: this.name,
              widgets: []
            })
          }
          this.onCancel()
        }
      })
    },
    /*     formValidated () {
      return Object.keys(this.fields).some(key => this.fields[key].validated) && Object.keys(this.fields).some(key =>
        this.fields[key].valid)
    }, */
    onCancel () {
      this.$emit('input', false)
    }
  }
}
</script>

<style scoped>
</style>
