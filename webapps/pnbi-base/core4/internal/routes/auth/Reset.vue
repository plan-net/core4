<template>
  <v-dialog
    v-model="dialogOpen"
    width="480px"
    persistent
  >
    <!-- after password reset started -->
    <v-card
      tile
      class="pa-3 auth-form-card"
    >
      <v-card-title class="py-0 pb-2 pt-2">
        <h2 class="title"><!-- Passwort zurücksetzen -->
        {{$t('resetPassword')}}
        </h2>
      </v-card-title>
      <v-card-text class="pt-2 pb-4">

        <v-text-field
          class="mb-3"
          autofocus
          clearable
          :label="$t('newPassword')"
          v-model.lazy="password"
          :error-messages="errors.collect($t('newPassword'))"
          :data-vv-as="$t('newPassword')"
          :data-vv-name="$t('newPassword')"
          v-validate="'required|passwordscore'"
          :append-icon="passwordVisible ? 'visibility' : 'visibility_off'"
          @click:append="passwordVisible = !passwordVisible"
          :type="passwordVisible ? 'text' : 'password'"
        ></v-text-field>

        <v-text-field
          class="mb-4"
          clearable
          :label="$t('repeatPassword')"
          v-model.lazy="password2"
          :error-messages="errors.collect($t('repeatPassword'))"
          :data-vv-as="$t('repeatPassword')"
          :data-vv-name="$t('repeatPassword')"
          required
          v-validate="'confirmspecial'"
          :append-icon="passwordVisible ? 'visibility' : 'visibility_off'"
          @click:append="passwordVisible = !passwordVisible"
          :type="passwordVisible ? 'text' : 'password'"
        >
        </v-text-field>

        <password
          :password="password"
          @score="score = $event; $validator.validateAll()"
        ></password>
      </v-card-text>
      <v-card-actions>
        <v-layout column>
          <v-flex>
            <v-btn
              class="mb-3"
              color="primary"
              block
              @click="onClick"
              :disabled="disabled"
              type="button"
              @keyup.enter="onClick"
            >{{$t('requestNewPassword')}}</v-btn>
          </v-flex>
          <v-flex>
            <v-btn
              to="/login"
              flat
              block
            >{{$t('backToLogin')}}</v-btn>
          </v-flex>
        </v-layout>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
<script>
import Password from './PasswordStrengthMeter.vue'
import Auth from '../../../Auth'
export default {
  created () {
    this.$validator.extend('passwordscore', {
      validate: () => {
        return {
          valid: true // this.score > 1
        }
      }
    })
    this.$validator.extend('confirmspecial', {
      validate: () => {
        return {
          valid: this.password === this.password2
        }
      }
    })
  },
  components: {
    Password
  },
  data () {
    return {
      dialogOpen: true,
      score: null,
      passwordVisible: false,
      finished: false,
      error: null,
      password: null,
      password2: null
    }
  },
  computed: {
    disabled () {
      const pristine = Object.values(this.fields).filter(val => {
        return val.pristine
      }).length > 0
      return pristine || this.errors.any()
    }
  },
  methods: {
    onClick () {
      Auth.reset({
        password: this.password,
        token: this.$route.params.token
      }).then(val => {
        this.finished = true
      }, err => {
        this.error = err
        console.war(err)
        this.$nextTick(function () {
          this.$validator.validateAll()
        })
      }).catch((err) => {
        /// TODO: what can happen? error neccessary?
        this.error = err
        console.war(err)
        this.$nextTick(function () {
          this.$validator.validateAll()
        })
      })
    }
  }

}
</script>
<style lang="css" scoped>
.password-strength-card {
  position: absolute;
  top: 26px;
  left: 426px;
}
/* .v-timeline-item .v-card:before {
  border-right-color: #999;
}
.v-timeline-item .v-card:after,
.v-timeline-item .v-card:before {
  top: 18px !important;
} */
/* div >>> .v-dialog--active {
  overflow: initial;
} */
</style>
