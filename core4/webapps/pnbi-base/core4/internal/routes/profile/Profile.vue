  <template>
    <pnbi-page header-type="2" small>
      <pnbi-card headline="Profile">
        <!-- Reset password: to be implemented
        <div slot="primary-controls">
          <v-btn color="primary">
            <v-icon left>vpn_key</v-icon>Password reset</v-btn>
        </div>
        -->
        <v-layout row wrap>
          <v-flex xs12 class="ml-0">
            <v-layout row  align-center justify-start fill-height>
            <v-icon class="mr-2">account_box</v-icon>
            <span class="mr-3">
              <div class="title">{{profile.name}}</div>
              <div class="subtitle grey--text">{{profile.realname}}</div>
            </span>
            <v-chip  v-if="profile.admin" color="accent" text-color="white">ADMIN</v-chip>
            </v-layout>
          </v-flex>
          <v-flex xs12 class="pt-3 mt-3" style="padding-left: 80px; border-top: 1px solid rgba(0,0,0,0.37)">
            <v-layout row wrap class="ml-3 profile-container">
              <v-flex xs2>Email:</v-flex>
              <v-flex xs10 class="pl-1">{{profile.email}}
                <v-icon v-if="profile.email === 'No email'" color="orange" small>warning</v-icon>
              </v-flex>
<!--               <v-flex xs1>Language:</v-flex>
              <v-flex xs11 class="pl-1">{{profile.language}}
              </v-flex> -->
              <v-flex xs2>Permissions:</v-flex>
              <v-flex xs10 class="mt-1">
                <div  v-if="profile.perm">
                  <v-chip class="mx-1" outline v-for="item in profile.perm" :key="item.name">{{item}}</v-chip>
                </div>
              </v-flex>

            </v-layout>
          </v-flex>
        </v-layout>
      </pnbi-card>
    </pnbi-page>
  </template>

<script>
import { mapGetters } from 'vuex'
export default {
  ...mapGetters([
    'profile'
  ]),
  computed: {
    profile () {
      return this.$store.getters.profile
    }
  },
  props: {
    type: String
  }
}

</script>
  <style lang="scss" scoped>
  .v-icon.material-icons {
    font-size: 90px;
  }
  .profile-container {
    > div {
      margin: 15px 0 15px 0;
    }
  }
  .v-chip {
    font-weight: 700 !important;
  }
  </style>
