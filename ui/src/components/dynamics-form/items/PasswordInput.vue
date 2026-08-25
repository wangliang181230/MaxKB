<template>
  <el-input v-bind="$attrs" :show-password="true" :autocomplete="autocomplete"></el-input>
</template>
<script setup lang="ts">
defineProps<{
  autocomplete?: string
}>()
</script>
<style lang="scss"></style>
