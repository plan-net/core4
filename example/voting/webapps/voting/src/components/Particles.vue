<template>
  <div id="particles">

  </div>
</template>

<script>
import './sketch.js'
// const COLOURS = ['#69D2E7', '#A7DBD8', '#E0E4CC', '#F38630', '#FA6900', '#FF4E50', '#F9D423']
import {
  mapGetters
} from 'vuex'

function Particle (x, y, radius) {
  this.init(x, y, radius)
}

Particle.prototype = {

  init: function (x, y, radius) {
    this.alive = true
    this.radius = radius || 10
    this.wander = 0.15
    this.theta = window.random(window.TWO_PI)
    this.drag = 0.92
    this.color = '#fff'
    this.x = x || 0.0
    this.y = y || 0.0
    this.vx = 0.0
    this.vy = 0.0
  },

  move: function () {
    this.x += this.vx
    this.y += this.vy
    this.vx *= this.drag
    this.vy *= this.drag
    this.theta += window.random(-0.5, 0.5) * this.wander
    this.vx += window.sin(this.theta) * 0.1
    this.vy += window.cos(this.theta) * 0.1

    this.radius *= 0.96
    this.alive = this.radius > 0.5
  },
  draw: function (ctx) {
    ctx.beginPath()
    ctx.arc(this.x, this.y, this.radius, 0, window.TWO_PI)
    ctx.fillStyle = this.color
    ctx.fill()
  }
}
const MAX_PARTICLES = 280
// const COLOURS = ['#d70f14']
const COLOURS = ['#3f515d']
export default {
  watch: {
    votes (newVal) {
      if (newVal) {
        this.spawn(window.random(window.innerWidth), window.random(window.innerHeight))
        this.spawn(window.random(window.innerWidth), window.random(window.innerHeight))
        this.spawn(window.random(window.innerWidth), window.random(window.innerHeight))
      }
    }
  },
  computed: {
    ...mapGetters(['question']),
    votes () {
      try {
        return this.question.n || 0
      } catch (err) {}
      return 0
    }
  },
  mounted () {
    /* eslint-disable */
      this.demo = Sketch.create({
        container: document.getElementById('particles'),
        retina: 'auto'
      })
      this.demo.spawn = this.spawn
      this.demo.update = this.update
      this.demo.draw = this.draw
      // this.demo.mousemove = this.mousemove
 /*      this.$bus.$on('SPAWN', function () {
        this.spawn(window.random(window.innerWidth), window.random(window.innerHeight))
      }.bind(this)) */
/*       window.setInterval(function () {
        this.spawn(window.random(window.innerWidth), window.random(window.innerHeight))
      }.bind(this), 500) */
    },
    data() {
      return {
        demo: null,
        particles: [],
        pool: []
      }
    },
    /* eslint-enable */
  methods: {
    spawn (x, y) {
      let particle, theta, force
      if (this.particles.length >= MAX_PARTICLES) {
        this.pool.push(this.particles.shift())
      }

      particle = this.pool.length ? this.pool.pop() : new Particle()
      particle.init(x, y, window.random(120, 150))

      particle.wander = 5// window.random(0.5, 2.0)
      particle.color = window.random(COLOURS)
      particle.drag = window.random(0.9, 0.99)

      theta = window.random(window.TWO_PI)
      force = window.random(2, 8)

      particle.vx = window.sin(theta) * force
      particle.vy = window.cos(theta) * force

      this.particles.push(particle)
    },
    update () {
      let i, particle
      for (i = this.particles.length - 1; i >= 0; i--) {
        particle = this.particles[i]
        if (particle.alive) {
          particle.move()
        } else {
          this.pool.push(this.particles.splice(i, 1)[0])
        }
      }
    },
    draw () {
      this.demo.globalCompositeOperation = 'lighter'

      for (var i = this.particles.length - 1; i >= 0; i--) {
        this.particles[i].draw(this.demo)
      }
    }

  }
}

</script>

<style scoped>
  #particles {
    opacity: .5;
    position: fixed;
    left: 1px;
    right: 1px;
    bottom: 1px;
    top: 52px;
    pointer-events: none;
  }

</style>
