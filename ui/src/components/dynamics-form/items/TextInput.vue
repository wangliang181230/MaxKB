<template>
  <el-input ref="inputRef" v-bind="$attrs" />
</template>
<script setup lang="ts">
import { ref } from 'vue'
const inputRef = ref()
defineExpose({ focus: () => inputRef.value?.focus() })
</script>
<style lang="scss"></style>
