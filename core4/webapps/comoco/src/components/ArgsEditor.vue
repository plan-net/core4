<template>
  <validation-observer
    ref="observer"
    v-slot="{  }"
  >
    <!-- , nlcerror: customErrors -->
    <validation-provider
      v-slot="{ errors }"
      :rules="{ required: (args || '').length > 0}"
      name="Args"
    >
      <v-row
        :class="{disabled: disabled}"
        v-if="args != null"
        no-gutters
        class="pt-0 px-0 editor-container"
      >
        <v-col
          cols="12"
          class="py-0"
        >
          Args
          <span class="pl-3 error--text">{{ errors[0] }}</span>
        </v-col>
        <v-row>
          <v-col
            cols="8"
            class="py-0 ace-container"
          >
            <ace-editor
              :disabled="disabled"
              height="140px"
              language="yaml"
              v-model="args"
            />
            <v-chip class="language-chip"
            small
            label
          >yaml</v-chip>
          </v-col>
          <v-col
            style="pointer-events: none;"
            cols="4"
            class="json py-0"
          >
            <div>
              <pre>{{json}}</pre>
            </div>
          </v-col>
        </v-row>

      </v-row>
    </validation-provider>
  </validation-observer>
</template>

<script>

import yaml from 'js-yaml'
import { ValidationProvider, ValidationObserver } from 'vee-validate'
import AceEditor from '@/components/AceEditor.vue'
let unwatch2
export default {
  props: {
    disabled: {
      type: Boolean,
      default: false,
      required: true
    }
  },
  beforeDestroy () {
    unwatch2 && unwatch2.dispose()
    this.args = null
  },
  async mounted () {
    await this.$nextTick()
    this.args = ''
    /*     this.args = `---
    sleep: 4000
    id: ${(Math.round(Math.random() * 10000))}` */
  },
  methods: {

  },
  components: {
    ValidationProvider,
    ValidationObserver,
    AceEditor
  },
  data () {
    return {
      args: null,
      editor: null
    }
  },
  watch: {
    args (newValue, oldValue) {
      this.$emit('change', newValue)
    }
  },
  computed: {
    json () {
      return yaml.safeLoad(this.args)
    }
  }
}
</script>

<style lang="scss" scoped>
.ace-container{
  position: relative;
}

.language-chip{
  position: absolute;
  bottom: 3px;
  right: 28px;
}

.json div {
  border: 1px solid rgba(0, 0, 0, 0.2);
  width: 100%;
  height: 100%;
  padding: 3px;
  overflow: scroll;
}
.editor-container {
  height: 140px;
  min-height: 140px;
}
.editor {
  border: 1px solid rgba(0, 0, 0, 0.2);
  width: 100%;
  height: 100%;
  min-height: 140px;
}
.disabled {
  pointer-events: none;
}
</style>
