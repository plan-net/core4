<template>
  <c4-page>
    <v-row
      justify="end"
      class="pr-5 pb-3 pl-5"
    >
      <start-job />
    </v-row>
    <v-layout column>
      <v-flex
        v-for="(notification, key) in notifications"
        :key="key"
      >
        <c4-notification
          v-if="notification.inComponents.includes('home')"
          @timeout-handler="notificationUpdateHandler"
          :show="notification.state"
          :type="notification.type"
          :message="notification.message"
          :dismissible="notification.dismissible"
          :timeout="notification.timeout"
          :name="key"
        >
          <component :is="notification.slot"></component>
        </c4-notification>
      </v-flex>

      <v-flex>
        <v-row no-gutters>
          <v-col
            cols="12"
            md="4"
            class="px-2 pb-2"
            v-for="(states, group) in groupsJobsByStates"
            :key="group"
          >
            <board
              :name="group"
              :flags="flags"
              :states="states"
            ></board>
          </v-col>
        </v-row>

      </v-flex>
      <v-flex
        v-if="stockChartVisible"
        ma-2
        hidden-sm-and-down
      >
        <stock-chart
          :isDark="dark"
          :key="dark"
        ></stock-chart>
      </v-flex>
      <v-btn v-else
        class="toggleIcon"
        @click="$store.dispatch('app/toggleChartVis')"
        large
        icon
      >
        <v-icon large>mdi-chevron-up</v-icon>
      </v-btn>
    </v-layout>
    <job-detail />
    <confirm-dialog ref="confirm" />
  </c4-page>
</template>

<script>
import { mapState, mapMutations, mapGetters } from 'vuex'

import JobDetail from '@/components/JobDetail'
import ConfirmDialog from '@/components/misc/ConfirmDialog'
import { NOTIFICATION_CHANGE_STATE } from '../store/comoco.mutationTypes'

import { groupsJobsByStates, jobFlags } from '../settings'

import Board from '@/components/Board'
import StockChart from '@/components/chart/StockChart'
import SocketReconnectError from '@/components/notifications/SocketReconnectError'
import StartJob from '@/components/StartJob.vue'

export default {
  mounted () {
    this.$root.$confirm = this.$refs.confirm
  },
  name: 'home',
  components: {
    ConfirmDialog,
    JobDetail,
    SocketReconnectError,
    Board,
    StockChart,
    StartJob
  },
  data () {
    return {
      groupsJobsByStates: groupsJobsByStates, // {waiting: [pending, ..., failed], running: [running], stopped: [error, ..., killed]
      flags: jobFlags // Z R N K
    }
  },
  methods: {
    ...mapMutations({
      notificationUpdate: NOTIFICATION_CHANGE_STATE
    }),
    notificationUpdateHandler (event, data) {
      this.notificationUpdate({ name: event, data: data })
    }
  },
  computed: {
    ...mapState({
      notifications: (state) => state.history.notifications,
      socketConnected: (state) => state.history.socket.isConnected
    }),
    ...mapGetters(['dark']),
    ...mapGetters('app', [
      'stockChartVisible'
    ])
  },
  watch: {
    socketConnected (newValue) {
      const data = {
        state: false
      }

      if (!newValue) {
        data.state = true
        data.type = 'error'
        data.slot = 'socketReconnectError'
      }

      this.notificationUpdateHandler('socket_reconnect_error', data)
    }
  }
}
</script>

<style scoped lang="scss">
.flex-equal-size {
  flex: 1 1 0;
}
.toggleIcon{
  position: absolute;
  right: 12px;
  bottom: 15px;
}
</style>
