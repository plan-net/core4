<template>
  <v-layout class="sidenav" row>
    <v-flex>
      <v-list dense class="grey lighten-4 pb-0">
        <v-list-tile to="/">
          <v-list-tile-action>
            <v-icon>list_alt</v-icon>
          </v-list-tile-action>
          <v-list-tile-content>
            <v-list-tile-title class="text--accent-4">
              Admin
            </v-list-tile-title>
          </v-list-tile-content>
        </v-list-tile>

        <v-list-tile to="/question">
          <v-list-tile-action>
            <v-icon>list_alt</v-icon>
          </v-list-tile-action>
          <v-list-tile-content>
            <v-list-tile-title class="text--accent-4">
              Voting
            </v-list-tile-title>
          </v-list-tile-content>
        </v-list-tile>

        <v-list-tile to="/result">
          <v-list-tile-action>
            <v-icon>list_alt</v-icon>
          </v-list-tile-action>
          <v-list-tile-content>
            <v-list-tile-title class="text--accent-4">
              Results
            </v-list-tile-title>
          </v-list-tile-content>
        </v-list-tile>
      </v-list>
    </v-flex>
  </v-layout>
</template>
