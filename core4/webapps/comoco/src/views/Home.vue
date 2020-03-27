<template>
  <c4-page>
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
        <v-layout
          row
          wrap
          xs12
        >
          <v-flex
            v-for="(states, group) in groupsJobsByStates"
            :key="group"
            class="ma-2 flex-equal-size"
          >
            <board
              xs12
              md4
              lg4
              xl4
              :name="group"
              :flags="flags"
              :states="states"
              class="pa-3"
            ></board>
          </v-flex>
        </v-layout>
      </v-flex>
      <v-flex
        ma-2
        hidden-sm-and-down
      >
        <stock-chart></stock-chart>
      </v-flex>
    </v-layout>
  </c4-page>
</template>

<script>
import { mapState, mapMutations } from 'vuex'

import { NOTIFICATION_CHANGE_STATE } from '../store/comoco.mutationTypes'

import { groupsJobsByStates, jobFlags } from '../settings'

import Board from '@/components/Board'
import stockChart from '@/components/StockChart'
import SocketReconnectError from '@/components/notifications/SocketReconnectError'

export default {
  name: 'home',
  components: {
    SocketReconnectError,
    Board,
    stockChart
  },
  data () {
    return {
      groupsJobsByStates: groupsJobsByStates, // {waiting: [pending, ..., failed], running: [running], stopped: [error, ..., killed]
      flags: jobFlags, // Z R N K
      dark: false
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
      notifications: (state) => state.notifications,
      socketConnected: (state) => state.socket.isConnected
    })
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
</style>
