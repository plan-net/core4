<template>
  <ace-editor
    id="editor"
    v-model="internalValue"
    @init="editorInit"
    :lang="language"
    :theme="theme"
    width="100%"
    :height="height"
  ></ace-editor>
</template>

<style lang="scss" scoped>
.theme--dark {
  label {
    color: var(--v-secondary-lighten5);
  }
}
.theme--light {
  label {
    color: var(--v-secondary-lighten1);
  }
}
</style>

<script>
import AceEditor from 'vue2-ace-editor'
let internalEditor = null
export default {
  name: 'ace-editor-wrapper',
  components: {
    AceEditor
  },

  computed: {
    theme () {
      return this.$store.getters.dark ? 'monokai' : 'xcode'
    },
    internalValue: {
      get: function () {
        return this.value
      },
      set: function (newValue) {
        this.$emit('input', newValue)
      }
    }
  },
  props: {
    /**
       * v-model
       */
    value: {
      type: String,
      default: ''
    },
    label: {
      type: String,
      default: 'Settings'
    },
    language: {
      type: String,
      default: 'yaml',
      required: true
    },
    disabled: {
      type: Boolean,
      default: false,
      required: false
    },
    /*     errorMessages: {
      type: Array,
      default: () => [],
      required: true
    }, */
    height: {
      type: String,
      default: '760px',
      required: false
    },
    fontFamily: {
      type: String,
      default: undefined,
      required: false
    }
  },
  watch: {
    disabled (newValue, oldValue) {
      this.updateEditor({
        readOnly: newValue
      })
    }
  },
  methods: {
    updateEditor (options) {
      internalEditor.setOptions(options)
    },
    editorInit (editor) {
      internalEditor = editor
      this.updateEditor({
        readOnly: this.disabled,
        vScrollBarAlwaysVisible: true,
        fontFamily: this.fontFamily,
        fontSize: '13px',
        wrap: true
      })
      /*       if (this.disabled === true) {
        editor.setReadonly(true)
        console.log(editor.setReadonly)
      } */

      require('brace/ext/language_tools') // language extension prerequsite...
      require(`brace/mode/${this.language}`)
      require(`brace/theme/${this.theme}`)
    }
  },
  data () {
    return {
    }
  }
}
</script>
