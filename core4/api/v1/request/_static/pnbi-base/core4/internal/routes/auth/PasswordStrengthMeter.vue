<template>
  <!--   <div class="Password pt-1">
    <div class="Password__strength-meter">
      <div class="Password__strength-meter--fill" :data-score="passwordStrength"></div>
    </div>
      <div class="Password__label grey--text pt-1">{{feedback.warning}}</div>
      <ul>
        <li v-for="suggestion in feedback.suggestions" :key="suggestion">{{suggestion}}</li>
      </ul>
  </div> -->
<!--   <v-alert :data-score="passwordStrength" :value="true" class="pt-2 pb-2">
      <h3 class="subheading">Password strength: <strong>{{passwordStrength}}</strong></h3>
      <p class="mt-2 mb-1">{{feedback.warning}}</p>
      <ul class="mt-1">
        <li v-for="suggestion in feedback.suggestions" :key="suggestion">{{suggestion}}</li>
      </ul>
  </v-alert> -->
  <div class="Password mt-2">
    <div class="Password__strength-meter">
      <div class="Password__strength-meter--fill" :data-score="passwordStrength"></div>
    </div>
    <div style="position: absolute; top: 4px;" class="grey--text caption"><!-- Passwortsicherheit -->{{$t('passwordSecurity')}}</div>
    <div class="Password__score pr-2">
      <div class="text-xs-right">
        <div class="caption Password__score--0" v-if="passwordStrength === 0">{{$t('pw.0')}}</div>
        <div class="caption Password__score--1" v-else-if="passwordStrength === 1">{{$t('pw.1')}}</div>
        <div class="caption Password__score--2" v-else-if="passwordStrength === 2">{{$t('pw.2')}}</div>
        <div class="caption Password__score--3" v-else-if="passwordStrength === 3">{{$t('pw.3')}}</div>
        <div class="caption Password__score--4" v-else-if="passwordStrength === 4">{{$t('pw.4')}}</div>
      </div>
    </div>
  </div>
</template>
<script>
export default {

  props: {
    id: {
      type: String,
      default: 'password'
    },
    password: {
      type: String
    },
    secureLength: {
      type: Number,
      default: 7
    }
  },
  data () {
    return {
      feedback: 'Passwortstärke'

    }
  },

  methods: {},

  computed: {
    passwordStrength () {
      return this.password ? window.zxcvbn(this.password).score : null
    },
    isSecure () {
      return this.password ? this.password.length >= this.secureLength : null
    },
    passwordCount () {
      return this.password && (this.password.length > this.secureLength ? `${this.secureLength}+` : this.password.length)
    }
  },

  watch: {
    passwordStrength (score) {
      this.$emit('score', score)
      this.feedback = window.zxcvbn(this.password).feedback
    }
  }
}
</script>

<style lang="scss">

  .Password {
    width: 100%;
    margin: 0 0 12px 0;
    position: relative;
  }

  .Password__score {
    position: absolute;
    right: 0;
  }
  .Password__strength-meter {
    position: relative;
    height: 3px;
    background: #DDD;
    margin: 0 6px 0 0;
    border-radius: 3px;
  }

  .Password__strength-meter--fill {
    background: transparent;
    height: inherit;
    position: absolute;
    width: 0;
    border-radius: inherit;
    transition: width 0.5s ease-in-out, background 0.25s;
  }

  .Password__strength-meter--fill[data-score='0'],
    {
    background: #ff6400;
    width: 20%;
  }

  .Password__strength-meter--fill[data-score='1'] {
    background: #f4ce42;
    width: 40%;
  }

  .Password__strength-meter--fill[data-score='2'] {
    background: #a4539c;
    width: 60%;
  }

  .Password__strength-meter--fill[data-score='3'] {
    background: #146624;
    width: 80%;
  }

  .Password__strength-meter--fill[data-score='4'] {
    background: #64a505;
     width: 100%;
  }
  .Password__score--0{
    color: #ff6400;
  }
  .Password__score--1{
    color: #f4ce42;
  }
  .Password__score--2{
    color: #a4539c;
  }
  .Password__score--3{
    color: #146624;
  }
  .Password__score--4{
    color: #64a505;
  }
</style>
