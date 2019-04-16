import { axiosInternal } from 'pnbi-base/core4/internal/axios.config.js'
import store from '@/store.js'
const api = {
  createBoard (dto) {
    const board = dto.board
    const allBoards = dto.boards
    allBoards.push(board)
    return this._putBoards({ boards: allBoards })
  },
  updateBoard (dto) {
    return this._putBoards(dto)
  },
  getBoards (dto) {
    return axiosInternal
      .get(`/setting/core_widgets`)
      .then(result => {
        if (result.data.boards == null) {
          // initialize, so we can use put
          /*           axiosInternal
            .post('/setting/core_widgets', { data: { boards: [] } })
            .then(result => {})
            .catch(error => Promise.reject(error)) */
          return []
        }
        return result.data.boards
      })
      .catch(error => {
        console.log(error)
        return Promise.reject(error)
      })
  },
  _putBoards (data) {
    return axiosInternal
      .put(`/setting/core_widgets`, { data })
      .then(result => {
        return true
      })
      .catch(error => {
        console.log(error)
        return Promise.reject(error)
      })
  },
  deleteBoard (dto) {
    const board = dto.board
    const allBoards = dto.boards
    return this._putBoards({ boards: allBoards.filter(val => val.name !== board.name) })
  },
  addToBoard (dto) {
    const { board, widgetId, boards } = dto
    boards.find(val => val.name === board.name).widgets.push(widgetId)
    return this._putBoards({ boards })
  },
  getWidgets () {
    return axiosInternal
      .get(`/info`, { params: { per_page: 1000, page: 0 } })
      .then(result => {
        const token = `?token=${JSON.parse(window.localStorage.getItem('user')).token}`
        const widgets = result.data
        let endpoint
        let pathEnd
        return widgets.map(val => {
          endpoint = {}
          pathEnd = `${val.rsc_id}${token}`
          endpoint.card_url = `${val.endpoint[0]}/info/card/${pathEnd}`
          endpoint.enter_url = `${val.endpoint[0]}/info/enter/${pathEnd}`
          endpoint.help_url = `${val.endpoint[0]}/info/help/${pathEnd}`
          val.endpoint = endpoint
          delete val.project
          delete val.started_at
          delete val.created_at
          return val
        })
      })
      .catch(error => Promise.reject(error))
  }
}

// no additional request - just interceptors for getting boards on first contact
axiosInternal.interceptors.response.use(
  response => {
    return response
  }, error => {
    // First load of the widget app
    if (
      error.config.url.includes(`${window.APIBASE_CORE}/setting`) &&
      // error.config.url.includes('core4/api/v1/setting') &&
      error.config.method === 'get' &&
      error.response.status === 400
    ) {
      const boards = [{ name: 'First board', widgets: [] }]
      axiosInternal
        .post('/setting/core_widgets', { data: { boards } })
        .then(result => {
          store.dispatch('setBoards', boards)
        })
        .catch(error => Promise.reject(error))
    } else {
      return Promise.reject(error)
    }
  }
)
export default api
