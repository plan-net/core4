<template>
  <c4-webapp :full-width="true" :nav-button-visible="false">
    <div slot="router">
      <transition name="fade" mode="out-in" :duration="{ enter: 200, leave: 300 }">
        <router-view/>
      </transition>
    </div>
  </c4-webapp>
</template>
<script>

export default {
  name: 'CORE4OS'
}
</script>
<style lang="scss">

</style>
