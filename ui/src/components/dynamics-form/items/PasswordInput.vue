<template>
  <el-input ref="inputRef" v-bind="$attrs" :show-password="true" :autocomplete="autocomplete"></el-input>
</template>
<script setup lang="ts">
import { ref } from 'vue'
defineProps<{
  autocomplete?: string
}>()
const inputRef = ref()
defineExpose({ focus: () => inputRef.value?.focus() })
</script>
<style lang="scss"></style>
