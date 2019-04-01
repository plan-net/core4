let scrollHeader = null
let tbody = null
let scrollHeaderClone = null
let datatable = null
const HEADER_OFFSET = 65
export default {
  props: {
    fixedHeader: {
      type: Boolean,
      default: false
    }
  },
  mounted () {
    this.$nextTick(function () {
      const fixedHeader = this.fixedHeader
      console.log('fixedHeader', fixedHeader)
      const fixedFooter = this.fixedFooter
      if (fixedHeader || fixedFooter) {
        datatable = this.$el.querySelector('.v-datatable')
        scrollHeader = this.$el.querySelector('.v-datatable > thead')
        tbody = this.$el.querySelector('tbody')
        window.addEventListener('scroll', this.throttle(this.handleScroll, 100))
        window.addEventListener('resize', this.throttle(this.handleResize, 100))
        this.handleScroll()
      }
    })
  },
  data () {
    return {
      headerIsFixed: false
    }
  },
  methods: {
    throttle (fn, wait) {
      var time = Date.now()
      return function () {
        if ((time + wait - Date.now()) < 0) {
          fn()
          time = Date.now()
        }
      }
    },
    handleResize (rect = tbody.getBoundingClientRect()) {
      if (this.headerIsFixed) {
        scrollHeader.style.width = Math.round(rect.width) + 'px'
        this.$nextTick(function () {
          const tds = tbody.querySelectorAll('tr:nth-child(1) > td')
          let resultTds = [].slice.call(tds).map(val => {
            return Math.floor(val.getBoundingClientRect().width)
          })
          scrollHeader.querySelectorAll('th').forEach(
            (val, index) => {
              val.style.width = resultTds[index] + 'px'
            }
          )
          scrollHeaderClone = scrollHeader.cloneNode(true)
          scrollHeaderClone.classList.add('bottom')
          scrollHeaderClone.style.bottom = 0
          scrollHeaderClone.style.top = 'auto'
          const bottom = this.$el.querySelector('.v-datatable > thead.bottom')
          if (bottom != null) {
            datatable.removeChild(bottom)
          }
          datatable.appendChild(scrollHeaderClone)
        })
      }
    },
    handleScroll (event) {
      const rect = tbody.getBoundingClientRect()
      if (rect.top < HEADER_OFFSET && this.headerIsFixed === false) {
        this.headerIsFixed = true
        scrollHeader.classList.add('pnbi-tablehead-fixed')

        this.handleResize(rect)
      } else if (rect.top >= HEADER_OFFSET && this.headerIsFixed === true) {
        this.headerIsFixed = false
        scrollHeader.classList.remove('pnbi-tablehead-fixed')
        const bottom = this.$el.querySelector('.v-datatable > thead.bottom')
        if (bottom != null) {
          datatable.removeChild(bottom)
        }
      }
    },
    destroyed () {
      window.removeEventListener('scroll', this.handleScroll)
      window.removeEventListener('resize', this.handleScroll)
    }
  }
}
