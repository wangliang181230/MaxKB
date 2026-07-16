<template>
  <el-card
    class="workflow-canvas-position"
    shadow="always"
    style="--el-card-padding: 5px 10px; --el-card-border-radius: 8px"
  >
    <div class="flex align-center">
      <el-text size="small" class="position-text">X: {{ view.x }}</el-text>
      <el-text size="small" class="position-text ml-8">Y: {{ view.y }}</el-text>
      <el-text size="small" class="position-text ml-8">
        {{ $t('workflow.control.zoom') }}: {{ view.zoom }}%
      </el-text>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ref, watch, onUnmounted } from 'vue'

// Props定义
interface Props {
  lf?: any
}
const props = withDefaults(defineProps<Props>(), {})

const view = ref({ x: 0, y: 0, zoom: 100 })

// 画布左上角在 graph 坐标系中的位置与当前缩放比例，只随平移/缩放变化
const syncPosition = () => {
  const container = props.lf?.container
  if (!props.lf || !container) {
    return
  }
  const rect = container.getBoundingClientRect()
  const { canvasOverlayPosition } = props.lf.graphModel.getPointByClient({
    x: rect.left,
    y: rect.top,
  })
  const scaleX = props.lf.graphModel.transformModel.SCALE_X
  view.value = {
    x: Math.round(canvasOverlayPosition.x),
    y: Math.round(canvasOverlayPosition.y),
    zoom: Math.round(scaleX * 100),
  }
}

// 重新渲染画布会换掉 LogicFlow 实例，必须先解绑旧实例的监听
let boundLf: any = null
const bind = () => {
  if (boundLf === props.lf) {
    return
  }
  if (boundLf) {
    boundLf.off('graph:transform', syncPosition)
  }
  boundLf = props.lf
  if (boundLf) {
    boundLf.on('graph:transform', syncPosition)
    syncPosition()
  }
}

watch(() => props.lf, bind, { immediate: true })

onUnmounted(() => {
  if (boundLf) {
    boundLf.off('graph:transform', syncPosition)
    boundLf = null
  }
})
</script>

<style scoped>
.workflow-canvas-position {
  position: absolute;
  top: 72px;
  left: 24px;
  z-index: 2;
  box-shadow: 0px 4px 8px 0px rgba(31, 35, 41, 0.1);
}
.position-text {
  font-variant-numeric: tabular-nums;
  color: var(--el-text-color-secondary);
}
</style>
