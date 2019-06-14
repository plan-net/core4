export default {
  queue: {
    // queue object interface:
    //   stat: {
    //     running: 0,
    //     pending: 0,
    //     deferred: 0,
    //     failed: 0,
    //     error: 0,
    //     inactive: 0,
    //     killed: 0,
    //     created: "2019-05-21T20:24:05.180000"
    //   },
    //   running: [],
    //   stopped: [],
    //   waiting: []
  },
  event: {
    // event object interface:
    //   running: 0,
    //   pending: 0,
    //   deferred: 0,
    //   failed: 0,
    //   error: 0,
    //   inactive: 0,
    //   killed: 0,
    //   created: "2019-05-21T20:24:05.180000"
  },
  socket: {
    isConnected: false,
    message: '',
    reconnectError: false
  },
  notifications: {
    socket_reconnect_error: {
      state: false, // false = hide, true = show
      type: 'error',
      dismissible: false, // show "close button" parameter
      // timeout: 7000,
      message: '',
      slot: '',
      inComponents: ['home']
    }
  }
}
