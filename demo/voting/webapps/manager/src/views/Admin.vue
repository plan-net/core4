<template>
  <pnbi-page header-type="3" small>
    <!--    <div slot="page-header-content">
    </div> -->
    <div>
      <question-crud :open="newQuestionDialogOpen" @close="newQuestionDialogOpen = false"></question-crud>
      <pnbi-datatable :headline="$route.meta.title" button-label="Neue Frage" @search="search = $event" @new="setCurrentItem">
        <!-- Optional Slot-->
        <div slot="primary-controls">
        </div>
        <!-- Optional Slot-->
        <div slot="secondary-controls">
        </div>

        <!-- Default Slot-->
        <v-data-table :headers="headers" :items="questions" :search="search" :rows-per-page-items="[10,25,50, {'text':'Alle','value':-1}]"
          rows-per-page-text="Elemente pro Seite">
          <template slot="items" slot-scope="props">
            <tr @click="$router.push(`question/${props.item.session_id}`)">

              <td>
                <pre></pre>
                <v-icon small class="mr-2">
                  question_answer
                </v-icon>{{props.item.question}}</td>
              <td class="text-xs-right">
                <v-layout align-center justify-end row fill-height class="pnbi-button-bar">
                  <v-tooltip bottom>
                    <v-btn slot="activator" small flat icon :to="`result/${props.item.session_id}`">
                      <v-icon small class="grey--text">
                        bar_chart
                      </v-icon>
                    </v-btn>
                    <span>Ergebnisse</span>
                  </v-tooltip>
                  <v-tooltip bottom>
                    <v-btn slot="activator" small flat icon @click.stop="$router.push(`question/${props.item.session_id}`)">
                      <v-icon small class="accent--text">
                        play_circle_filled
                      </v-icon>
                    </v-btn>
                    <span>Frage öffnen</span>
                  </v-tooltip>
                  <v-tooltip bottom>
                    <v-btn slot="activator" small flat icon @click.stop="setCurrentItem(props.item)">
                      <v-icon small class="grey--text">
                        edit
                      </v-icon>
                    </v-btn>
                    <span>Editieren</span>
                  </v-tooltip>
                  <v-tooltip bottom>
                    <v-btn small slot="activator" icon @click.stop="setDeleteItem(props.item)">
                      <v-icon small class="grey--text">delete
                      </v-icon>
                    </v-btn>
                    <span>Löschen</span>
                  </v-tooltip>
                </v-layout>
              </td>
            </tr>
          </template>
          <template slot="pageText" slot-scope="props">
            {{ props.pageStart }} - {{ props.pageStop }} von {{ props.itemsLength }}
          </template>
          <v-alert slot="no-results" :value="true" color="error" icon="warning">
            Keine Ergebnisse für "{{ search }}" gefunden.
          </v-alert>
          <template slot="no-data">
            <pnbi-empty text="Keine Datensätze vorhanden. Bitte erstellen sie ein neue Frage."></pnbi-empty>
          </template>
        </v-data-table>
      </pnbi-datatable>

    </div>
  </pnbi-page>
</template>
<script>
import QuestionCrud from '@/components/QuestionCrud'
import {
  mapGetters,
  mapActions
} from 'vuex'
export default {
  name: 'admin',
  components: {
    QuestionCrud
  },
  created () {},
  methods: {
    ...mapActions(['fetchQuestions', 'setCurrentQuestion']),
    setDeleteItem (item) {
      this.setCurrentQuestion(item)
      this.deleteDialogOpen = true
    },
    setCurrentItem (item) {
      this.setCurrentQuestion(item)
      this.newQuestionDialogOpen = true
    }
  },
  mounted () {
    this.fetchQuestions()
  },
  data () {
    return {
      search: null,
      headers: [{
        text: 'Frage',
        align: 'left',
        sortable: true,
        value: 'question'
      },
      {
        align: 'right',
        text: 'Aktionen',
        sortable: false
      }
      ],
      itemToDelete: null,
      deleteDialogOpen: false,
      newQuestionDialogOpen: false
    }
  },
  computed: {
    ...mapGetters(['questions'])
    /* ,
            newQuestionDialogOpen: {
              get: function (newVal) {
                return this.internalNewQuestionDialogOpen
              },
              set: function (newVal) {
                this.internalNewQuestionDialogOpen = newVal
              }
            } */
  }
}

</script>
