import { axiosInternal } from 'core4ui/core4/internal/axios.config.js'
// import store from '@/store'
const widgetPath = '/setting/core_widgets_next'
const api = {
  __createUser () {
    const data = {
      name: 'targobank_user',
      realname: 'targobank user',
      passwd: 'hans',
      email: 'test@mail.de',
      role: ['standard_user'],
      perm: ['app://store/targobank']
    }
    return axiosInternal.post('/roles', data).then(result => {
      return true
    })
  },
  __createStore () {
    const theme = {
      dark: {
        primary: '#FF0266',
        accent: '#03DAC5',
        secondary: '#424242',
        success: '#4CAF50',
        info: '#2196F3',
        warning: '#FB8C00',
        error: '#FF5252'
      },
      light: {
        primary: '#6200ee',
        accent: '#03DAC5',
        secondary: '#424242',
        success: '#4CAF50',
        info: '#2196F3',
        warning: '#FB8C00',
        error: '#FF5252'
      }
    }
    return axiosInternal
      .post('/store/targobank', { json: theme })
      .then(result => {
        return true
      })
  },
  __getStore () {
    return axiosInternal.put('/store/targobank').then(result => {
      return result.data
    })
  },
  createBoard (boards) {
    return this._putBoards({ boards })
  },
  updateBoard (dto) {
    return this._putBoards(dto)
  },
  _putBoards (data) {
    // console.log(data)
    return axiosInternal.put(widgetPath, { data }).then(result => {
      return true
    })
  },
  async fetchTags (dto) {
    try {
      const ret = await axiosInternal.get('/_info?tag')
      return ret.data
    } catch (err) {
      console.warn(err)
    }
  },
  async fetchBoards (dto) {
    try {
      const ret = await axiosInternal.get(widgetPath)
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
      tags: [],
      per_page: 2,
      page: 0
    }
  ) {
    const tmpParams = { per_page: params.per_page, page: params.page }
    const search = params.search
    /*     if (params.tags.length) {
      const tagArrStr = JSON.stringify(params.tags.map(t => t.value))
      const tag = `tag in ${tagArrStr}`
      search = search.length ? `${search} and ${tag}` : tag
    } */
    if ((search || '').length) {
      tmpParams.search = search
    }
    if (params.tags.length) {
      tmpParams.api = params.tags.find(val => !val.default) != null
      tmpParams.tag = JSON.stringify(params.tags.map(t => t.value))
    }
    console.log(tmpParams)
    try {
      const ret = await axiosInternal.get('/_info', {
        params: tmpParams
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
      .post(widgetPath, { data })
      .then(result => result)
      .catch(error => Promise.reject(error))
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
      window.location.reload()
    } else {
      return Promise.reject(error)
    }
  }
)
export default api
