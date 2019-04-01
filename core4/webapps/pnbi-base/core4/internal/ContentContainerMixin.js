/**
 * @mixin
 */
export default {
  props: {
    /**
     * Sets headline. Headline is bigger, bolder then title. Used as <strong>primary</strong> headline on a page.
     */
    headline: {
      default: '',
      type: String,
      required: false
    },
    /**
     * Sets title. Title is smaller, Usually used when there is already a card with headline on a page.
     */
    title: {
      required: false,
      type: String,
      default: ''
    }
  },

  mounted () {
    if (this.headline.length) {
      this.$el.querySelector('.card-headline').classList.add('headline')
    } else if (this.title.length) {
      this.$el.querySelector('.card-headline').classList.add('title')
    }
  },
  computed: {
    label () {
      const headline = this.headline.length
      const title = this.title.length
      if (headline) {
        return this.headline.toUpperCase()
      } else if (title) {
        return this.title.toUpperCase()
      }
    }
  }
}
