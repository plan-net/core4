import { axiosInternal } from 'core4ui/core4/internal/axios.config.js'
import store from '@/store'
const api = {
  createBoard (boards) {
    return this._putBoards({ boards })
  },
  updateBoard (dto) {
    return this._putBoards(dto)
  },
  _putBoards (data) {
    // console.log(data)
    return axiosInternal.put('/setting/core_widgets', { data }).then(result => {
      return true
    })
  },
  async fetchTags (dto) {
    // return ['All', 'New']
    try {
      const ret = await axiosInternal.get('/_info?tag')
      return ret.data
    } catch (err) {
      console.warn(err)
    }
  },
  async fetchBoards (dto) {
    try {
      const ret = await axiosInternal.get('/setting/core_widgets')
      return (
        ret.data || {
          boards: [],
          board: ''
        }
      )
    } catch (err) {
      console.warn(err)
    }
  },
  async searchWidgets (
    params = {
      search: '',
      per_page: 2,
      page: 0
    }
  ) {
    try {
      const ret = await axiosInternal.get('/_info', {
        params
      })
      return ret
    } catch (err) {
      console.warn(err)
    }
  },
  async persistOptions (
    data = {
      boards: [],
      board: null,
      sidebar: 1
    }
  ) {
    return axiosInternal
      .post('/setting/core_widgets', { data })
      .then(result => result)
      .catch(error => Promise.reject(error))
  },

  async fetchWidgets () {
    const fields = {
      title: 'String',
      qual_name: 'DotSeperated',
      tag: 'Array',
      decription: 'String',
      subtitle: 'String',
      author: 'String',
      container: 'Array'
    }
    function constructSearchString (widget) {
      let $search = ''
      Object.keys(fields).forEach(key => {
        if (widget[key] != null) {
          if (fields[key] === 'String') {
            $search += widget[key] + ' '
          } else if (fields[key] === 'Array') {
            if (key === 'container' && widget[key].length) {
              const tmp = (widget.container[0] || '').split('.')
              $search += tmp[tmp.length - 1] // core4.api.v1.server.CoreApiServer => CoreApiServer
            } else if (widget[key].length) {
              $search += widget[key].join(' ') + ' '
            }
          } else {
            const tmp = (widget.qual_name || '').split('.').join(' ') + ' '
            $search += tmp
          }
        }
      })
      /* replace words and whitespace */
      // $search = $search.replace(/ for| and| v1| api| request| core4/gi, '').replace(/\s+/g, ' ').trim()
      $search = $search
        .replace(/ for| and| v1| request/gi, '')
        .replace(/\s+/g, ' ')
        .trim()
      return Object.assign(widget, { $search: $search.split(' ') })
    }
    try {
      const w = await axiosInternal
        .get('/_info', { params: { per_page: 1000, page: 0 } })
        .then(result => {
          const user = JSON.parse(window.localStorage.getItem('user') || {})
          const token = `?token=${user.token || -1}`
          const widgets = result.data
          let endpoint
          let pathEnd
          return widgets.map(val => {
            const pre = val.endpoint[0].replace('5001', '8080')
            endpoint = {}
            pathEnd = `${val.rsc_id}${token}`
            endpoint.card_url = `${pre}/_info/card/${pathEnd}`
            endpoint.enter_url = `${pre}/_info/enter/${pathEnd}`
            endpoint.help_url = `${pre}/_info/help/${pathEnd}`
            val.endpoint = endpoint
            const vq = val.qual_name
            val.$qual_name =
              vq.substring(0, vq.indexOf('.')) +
              '…' +
              vq.substring(vq.lastIndexOf('.') + 1)
            val.doc =
              val.doc ||
              'Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor.'
            val.res = val.res || 11
            val.width = Number(val.res.toString().split('')[0])
            val.height = Number(val.res.toString().split('')[1])
            delete val.project
            delete val.started_at
            delete val.created_at
            return constructSearchString(val)
          })
        })

      return w
      // return w
    } catch (err) {
      console.warn(err)
    }
  }
}

// no additional request - just interceptors for getting boards on first contact
axiosInternal.interceptors.response.use(
  response => {
    return response
  },
  async error => {
    // First load of the widget app
    if (
      error.config.url.includes('/setting') &&
      error.config.method === 'get' &&
      error.response.status === 400
    ) {
      const boards = [{ name: 'First board', widgets: [] }]
      const data = {
        boards,
        board: boards[0].name,
        sidebar: 1,
        technical: false
      }
      await api.persistOptions(data)
      store.dispatch('setOptions', data)
    } else {
      return Promise.reject(error)
    }
  }
)
export default api
