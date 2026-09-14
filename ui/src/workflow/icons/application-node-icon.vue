<template>
  <el-avatar
    v-if="isAppIcon(item?.icon)"
    shape="square"
    :size="size || 32"
    style="background: none"
    class="mr-8"
  >
    <img :src="resetUrl(item?.icon || '', resetUrl('./favicon.ico'))" alt="" />
  </el-avatar>
  <LogoIcon v-else :height="`${size}px`" />
</template>
<script setup lang="ts">
import { isAppIcon, resetUrl } from '@/utils/common'
const props = defineProps<{
  item: {
    name: string
    icon: string
  }
  size?: string | number
}>()
</script>
