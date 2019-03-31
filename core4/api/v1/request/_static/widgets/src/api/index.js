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
          axiosInternal
            .post('/setting/core_widgets', { data: { boards: [] } })
            .then(result => {})
            .catch(error => Promise.reject(error))
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
        return widgets.map(val => {
          val.endpoint = val.endpoint[0]
          val.endpoint.card_url = `${val.endpoint.card_url}${token}`
          val.endpoint.enter_url = `${val.endpoint.enter_url}${token}`
          val.endpoint.help_url = `${val.endpoint.help_url}${token}`
          delete val.project
          delete val.route_id
          return val
        })
      })
      .catch(error => Promise.reject(error))
  }
}

// no additional request - just interceptors for getting boards on first contact
axiosInternal.interceptors.response.use(
  response => {
    /*     if (response.config.url.includes('core4/api/setting') && response.config.method === 'get') {
      const boards = response.data.data.core_widgets.boards
      if (boards != null) {
        store.dispatch('setBoards', boards)
      } else {
        axiosInternal
          .post('/setting/core_widgets', { data: { boards: [] } })
          .then(result => {
          })
          .catch(error => Promise.reject(error))
      }
    } */
    return response
  }, error => {
    // First load of the widget app
    if (
      error.config.url.includes('core4/api/setting') &&
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
