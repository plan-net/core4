import axios from 'axios'
export const instance = axios.create({
  baseURL: process.env.VUE_APP_APIBASE_CORE,
  headers: {
    common: { Accept: 'application/json' }
  }

})
/* ...mapActions('widgets', {
  removeFromBoard: 'removeFromBoard',
  fetchWidget: 'fetchWidget'
}),
import { axiosInternal } from 'core4ui/core4/internal/axios.config.js'
try {
  const widget = await axiosInternal.get(`_info/card/${this.widget.rsc_id}`,
    { headers: { common: { Accept: 'application/json' } } })
  console.log(widget)
} catch (err) {
  console.log('NotFound', this.widget)
} */
