import Vue from 'vue'
export const LOADING = 'LOADING'
export const PROFILE_UPDATED = 'PROFILE_UPDATED'
export const CONFIG_UPDATED = 'CONFIG_UPDATED'
export const ERROR = 'ERROR'
export const FORBIDDEN = 'FORBIDDEN'
export const TRACK = 'TRACK'

const EventBus = new Vue()
export default EventBus
