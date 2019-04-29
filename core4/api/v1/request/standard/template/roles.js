<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <title>Role Management</title>
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <link href="https://unpkg.com/vuetify@1.5.13/dist/vuetify.css" rel="stylesheet">
    <link href="https://bi.plan-net.com/cdn/assets/fonts/material-icons.css" rel="stylesheet">
    <style>
        .big-search {
            max-width:100% !important;
        }
    </style>
</head>

<body style="opacity: 0;">
    <div id="app">
        <v-app>
            <v-container fluid>
                <v-layout>
                    <v-flex>
                        <h1 class="headline mb-3">Roles overview</h1>
                    </v-flex>
                    <v-flex class="text-xs-right">
                        <v-btn small @click="isCreateDialogOpen=true; currentRole={};" color="primary">
                            <v-icon class="mr-1" small>
                                create
                            </v-icon>
                            Create Role
                        </v-btn>
                    </v-flex>
                </v-layout>
                <v-card>
                    <v-card-title class="text-xs-right">
                        <v-spacer v-if="!bigSearch"></v-spacer>
                        <v-text-field
                            :class="{'big-search':bigSearch}"
                            style="max-width:200px"
                            v-model="searchData"
                            prepend-icon="loupe"
                            append-icon="search"
                            label="Search"
                            @keyup.enter="update"
                            single-line
                            clearable
                            hide-details
                            @click:append="update"
                            @click:prepend="bigSearch=!bigSearch"
                        ></v-text-field>
                    </v-card-title>
                    <v-data-table flat v-if="roles" :loading="loading"
                    :pagination.sync="pagination"
                    :rows-per-page-items="[10, 25, 75]"
                    :total-items="pagination.totalItems"
                    :headers="headers"
                    :items="roles"
                    @update:pagination="update"
                    class="elevation-1">

                        <template v-slot:items="props">
                            <td class="text-xs-center">{{! props.item.name }}</td>
                            <td class="text-xs-center">{{! props.item.realname }}</td>
                            <td class="text-xs-center">
                                <v-icon v-if="props.item.is_active" small class="success--text">
                                    check
                                </v-icon>
                                <v-icon v-else small class="warning--text">
                                    remove_circle_outline
                                </v-icon>
                            </td>
                            <td class="text-xs-center">
                                <div v-if="props.item.perm.length" v-for="perm in props.item.perm">
                                    {{! perm }} </br>
                                </div>
                            </td>
                            <td class="text-xs-right">
                                <v-layout row>
                                    <v-flex xs5>
                                        <v-btn small @click="onCreateDialogOpen(props.item)" flat icon>
                                            <v-icon class="grey--text" small>
                                                edit
                                            </v-icon>
                                        </v-btn>
                                    </v-flex>
                                    <v-flex xs3>
                                        <v-btn small @click="deleteRole(props.item)" icon>
                                            <v-icon small class="grey--text">delete
                                            </v-icon>
                                        </v-btn>
                                    </v-flex>
                                </v-layout>
                            </td>
                        </template>
                        <template v-slot:pageText="props">
                        <pre>{{! props }}</pre>
                            {{! props.pageStart + 1 }} - {{! props.pageStop +1 }} of {{! props.itemsLength }}
                        </template>
                    </v-data-table>
                </v-card>
                <div>
                    <v-alert :value="error" type="error" dismissible >
                      {{! error}}</br>
                    </v-alert>
                </div>
            </v-container>
        </v-app>

        <v-dialog v-if="currentRole" v-model="isCreateDialogOpen" persistent max-width="600px">

            <v-card>
                <v-card-title v-if="currentRole._id">
                    Edit role
                </v-card-title>
                <v-card-title v-else>
                    Create Role
                </v-card-title>
                <v-card-text>

                    <v-form>
                        <v-layout class="pa-3 pl-5" column>
                            <v-text-field v-model="currentRole.name" label="Name"> </v-text-field>
                            <v-text-field v-model="currentRole.realname" label="Realname" required></v-text-field>
                            <v-text-field v-model="currentRole.email" label="E-Mail"></v-text-field>
                            <v-combobox
                                multiple
                                deletable-chips
                                small-chips
                                v-model="currentRole.perm"
                                label="Permissions">
                            </v-combobox>
                            <v-combobox
                                v-model="currentRole.role"
                                :items="distinctRoles"
                                attach
                                deletable-chips
                                small-chips
                                multiple
                                label="Roles"
                                flat
                            ></v-combobox>
                            <v-text-field
                                v-model="currentRole.password"
                                label="Password"
                                :append-icon="showPw ? 'visibility' : 'visibility_off'"
                                :type="showPw ? 'text': 'password'"
                                @click:append="showPw= !showPw"
                                ></v-text-field>
                            <v-checkbox v-model="currentRole.is_active" label="Active"></v-checkbox>
                        </v-layout>
                    </v-form>
                  <v-alert :value="error" type="error" dismissible>
                      {{! error}}</br>
                  </v-alert>

                </v-card-text>
                  <v-card-actions>
                    <v-spacer></v-spacer>
                    <v-btn color="primary" @click="isCreateDialogOpen=false;currentRole=null;error=null;">Cancel</v-btn>
                    <v-btn color="primary" @click="deleteRole(currentRole)">Delete</v-btn>
                    <v-btn color="primary" @click="submit(currentRole)">submit</v-btn>

                  <v-card-actions>
                 </v-card>
        </v-dialog>
    </div>
</body>

<script src="https://unpkg.com/vue@2.6.10/dist/vue.js"></script>
<script src="https://unpkg.com/vuetify@1.5.13/dist/vuetify.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/axios/0.18.0/axios.min.js"></script>

<script>
    const api = {
        getRoles: function(internalPagination) {
            return axios.get('/core4/api/v1/roles' + internalPagination
            )
            .then(
                function(result) {
                    return result
                })
        },
        getRole: function(role){
            return axios.get('/core4/api/v1/roles/' + role._id)
        },
        deleteRole: function(role) {
            return axios.delete('/core4/api/v1/roles/' + role._id + '?etag=' + role.etag).then(
                function(result) {
                    return result.data.data
                })
        },
        submitRole: function(role) {
            return axios.put('/core4/api/v1/roles/' + role._id, role);
        },
        createRole: function(role) {
            return axios.post('/core4/api/v1/roles', role);
        },
        distinctRoles: function() {
            console.warn("distinct roles")
            return axios.get('/core4/api/v1/roles/distinct');
        },

    }
    var app = new Vue({
        el: "#app",
        data: function() {
            return {
                headers: [{
                        text: 'Name',
                        value: 'name',
                        align: 'center'
                    }, {
                        text: 'Realname',
                        value: 'realname',
                        align: 'center',
                    }, {
                        text: 'Active',
                        value: 'is_active',
                        align: 'center'
                    },{
                        text: 'Perm',
                        value: 'perm',
                        align: 'center'
                    }, {
                        text: 'Actions',
                        value: '',
                        sortable: false,
                        align: 'center'
                    }
                ],
                isCreateDialogOpen: false,
                roles: [],
                currentRole: null,
                loading: false,
                error: null,
                searchData: null,
                bigSearch: false,
                distinctRoles: [],
                showPw: false,
                pagination: {
                    page: 1,
                    rowsPerPage: 25,
                    totalItems: 0,
                    sortBy: "_id",
                    descending: true,
                }
            }
        },
        beforeCreate: function() {},
        created: function() {},
        mounted: function() {
            document.querySelector('body').style.opacity = 1
            api.getRoles(this.internalPagination).then(function(roles) {
                this.pagination.totalItems = roles.data.total_count
                this.pagination.page = roles.data.page + 1
                this.pagination.rowsPerPageItems = roles.data.per_page
                this.roles = roles.data.data
            }.bind(this));
        },
        computed: {
        internalPagination : function(){
            ret =
            "?per_page="+ this.pagination.rowsPerPage +
            "&page=" + (this.pagination.page -1 )+
            "&order=" + (this.pagination.descending ? -1:1) +
            "&sort=" + this.pagination.sortBy

            if(this.searchData){
                ret = ret + "&filter=" + this.searchData
            }
            return ret

            }

        },
        watch: {
        },
        methods: {
            deleteRole: function(role) {
                this.loading = true;
                api.deleteRole(role).then(function(success) {
                    this.roles = this.roles.filter(function(elem) {
                        return role._id !== elem._id
                    })
                    this.isCreateDialogOpen = false;
                    this.currentRole = null;
                    this.loading = false;
                }.bind(this))
            },
            onCreateDialogOpen: function(role) {
                this.loading = true;
                if(role){
                    api.getRole(role)
                        .then(function(success){
                            role = success.data.data
                            this.currentRole = JSON.parse(JSON.stringify(role))
                            this.isCreateDialogOpen = true;
                            this.loading = false;
                            this.error = null;
                        }.bind(this))
                }
            },
            submit: function(roles) {
                console.log(roles.perm)
                this.loading = true;
                if (roles._id) {
                    api.submitRole(roles)
                        .then(function(success) {
                            console.warn(success)
                            this.updateRoles(success.data.data);
                            this.currentRole = null;
                            this.isCreateDialogOpen = false;
                            this.loading = false;
                            this.error = null;
                            this.getSelectRoles();
                        }.bind(this))
                        .catch(function(error){
                            this.error=error.response.data.error.split("File")[0];
                        }.bind(this))
                } else {
                    this.loading = true;
                    api.createRole(roles)
                        .then(function(success) {
                            console.warn(success.data.data)
                            this.roles.push(success.data.data)
                            this.currentRole = null;
                            this.isCreateDialogOpen = false;
                            this.loading = false;
                            this.error = null;
                            this.getSelectRoles();
                        }.bind(this))
                        .catch(function(error){
                            this.error=error.response.data.error.split("File")[0];
                        }.bind(this))

                }
            },
            updateRoles: function(role) {
                this.roles = this.roles.map(function(currentRole) {
                    if (role._id == currentRole._id) {
                        return role
                    }
                    return currentRole;
                })
            },
            update: function() {
                   this.loading = true;
                   console.warn("updatePaging")
                   api.getRoles(this.internalPagination).then(function(success) {
                       this.pagination.totalItems = success.data.total_count
                       this.roles = success.data.data
                       this.loading = false;
                       this.getSelectRoles();
                   }.bind(this))
                   .catch(function(error){
                        this.error = error.response.data.error.split("File")[0];
                        this.loading = false;
                    }.bind(this))

            },
            getSelectRoles: function(){
                api.distinctRoles().then(function(success){
                    this.distinctRoles = success.data.data
                }.bind(this))
                .catch(function(error){
                    this.error = error.response.data.error.split("File")[0];
                    this.loading = false
                }.bind(this))
            },
        }
    });

</script>

</html>