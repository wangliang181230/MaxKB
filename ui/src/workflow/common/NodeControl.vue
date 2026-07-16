<template>
  <el-card shadow="always" style="--el-card-padding: 8px 12px; --el-card-border-radius: 8px">
    <el-button
      @click="changeCursor(true)"
      style="border: none; padding: 4px; height: 24px"
      :class="{ 'is-drag-active': isDrag }"
    >
      <el-icon :size="16"><Position /></el-icon>
    </el-button>
    <el-button
      @click="changeCursor(false)"
      style="border: none; padding: 4px; height: 24px; margin-left: 8px"
      :class="{ 'is-drag-active': !isDrag }"
    >
      <AppIcon iconName="app-raisehand" :size="16"></AppIcon>
    </el-button>
    <el-divider direction="vertical" />
    <el-button link @click="undo" style="border: none" :disabled="!canUndo">
      <el-tooltip
        effect="dark"
        :content="$t('workflow.control.undo')"
        placement="top"
      >
        <el-icon :size="16"><RefreshLeft /></el-icon>
      </el-tooltip>
    </el-button>
    <el-button link @click="redo" style="border: none" :disabled="!canRedo">
      <el-tooltip
        effect="dark"
        :content="$t('workflow.control.redo')"
        placement="top"
      >
        <el-icon :size="16"><RefreshRight /></el-icon>
      </el-tooltip>
    </el-button>
    <el-divider direction="vertical" />
    <el-button link @click="zoomOut" style="border: none">
      <el-tooltip
        effect="dark"
        :content="$t('workflow.control.zoomOut')"
        placement="top"
      >
        <el-icon :size="16" :title="$t('workflow.control.zoomOut')"
          ><ZoomOut
        /></el-icon>
      </el-tooltip>
    </el-button>
    <el-button link @click="zoomIn" style="border: none">
      <el-tooltip
        effect="dark"
        :content="$t('workflow.control.zoomIn')"
        placement="top"
      >
        <el-icon :size="16" :title="$t('workflow.control.zoomIn')"
          ><ZoomIn
        /></el-icon>
      </el-tooltip>
    </el-button>
    <el-button link @click="fitView" style="border: none">
      <el-tooltip
        effect="dark"
        :content="$t('workflow.control.fitView')"
        placement="top"
      >
        <AppIcon
          iconName="app-fitview"
          :title="$t('workflow.control.fitView')"
        ></AppIcon>
      </el-tooltip>
    </el-button>
    <el-divider direction="vertical" />
    <el-button link @click="retract" style="border: none">
      <el-tooltip
        effect="dark"
        :content="$t('workflow.control.retract')"
        placement="top"
      >
        <AppIcon
          style="font-size: 16px"
          iconName="app-retract"
          :title="$t('workflow.control.retract')"
        ></AppIcon>
      </el-tooltip>
    </el-button>
    <el-button link @click="extend" style="border: none">
      <el-tooltip
        effect="dark"
        :content="$t('workflow.control.extend')"
        placement="top"
      >
        <AppIcon
          style="font-size: 16px"
          iconName="app-extend"
          :title="$t('workflow.control.extend')"
        ></AppIcon>
      </el-tooltip>
    </el-button>
    <el-button link @click="layout" style="border: none">
      <el-tooltip
        effect="dark"
        :content="$t('workflow.control.beautify')"
        placement="top"
      >
        <AppIcon
          style="font-size: 16px"
          iconName="app-beautify"
          :title="$t('workflow.control.beautify')"
        ></AppIcon>
      </el-tooltip>
    </el-button>
  </el-card>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
const props = defineProps({
  lf: Object || String || null,
})

const isDrag = ref(false)
const canUndo = ref(false)
const canRedo = ref(false)

/** 读取按钮状态 */
const updateHistoryState = () => {
  if (props.lf) {
    const lf = props.lf as any
    canUndo.value = lf.history?.undoAble() ?? false
    canRedo.value = lf.history?.redoAble() ?? false
  }
}

onMounted(() => {
  if (props.lf) {
    const lf = props.lf as any
    const history = lf.history
    if (!history) return

    const origAdd = history.add.bind(history)
    const origLfUndo = lf.undo.bind(lf)
    const origLfRedo = lf.redo.bind(lf)

    /**
     * 核心修复：阻止 undo/redo 后 debounced MobX reaction（100ms）调用 add。
     * 原始 add 内部会执行 this.redos=[] 和 emit history:change，
     * 导致栈被污染和按钮状态错误。
     * _skipNextAdd 标志让 debounced add 变成 no-op，保持栈干净。
     */
    let skipNextAdd = false

    history.add = function (data: any) {
      if (skipNextAdd) {
        skipNextAdd = false
        return // 完全跳过，不修改栈，不 emit 事件
      }
      origAdd(data)
    }

    /**
     * history:change 监听器：skipNextAdd 为 true 时不更新按钮状态。
     * 虽然我们的 add 覆盖会跳过 debounced add，但作为安全措施，
     * 防止任何意外事件触发错误的按钮状态。
     */
    const onHistoryChange = () => {
      if (skipNextAdd) return
      updateHistoryState()
    }

    lf.undo = function () {
      origLfUndo()
      skipNextAdd = true // 标记：阻止后续的 debounced add
      updateHistoryState()
    }

    lf.redo = function () {
      origLfRedo()
      skipNextAdd = true
      updateHistoryState()
    }

    lf.on('history:change', onHistoryChange)
    updateHistoryState()
  }
})

onUnmounted(() => {
  if (props.lf) {
    const lf = props.lf as any
    lf.off('history:change', updateHistoryState)
  }
})

function undo() {
  props.lf?.undo()
}
function redo() {
  props.lf?.redo()
}

function zoomIn() {
  props.lf?.zoom(true, [0, 0])
}
function zoomOut() {
  props.lf?.zoom(false, [0, 0])
}
function fitView() {
  props.lf?.resetZoom()
  props.lf?.resetTranslate()
  props.lf?.fitView()
}
const layout = () => {
  props.lf?.extension.dagre.layout()
  props.lf?.graphModel.nodes.forEach((node: any) => {
    if (node.type === 'loop-body-node') {
      node?.loopLayout?.()
    }
  })
}
const retract = () => {
  props.lf?.graphModel.nodes.forEach((element: any) => {
    element.properties.showNode = false
  })
}
const extend = () => {
  props.lf?.graphModel.nodes.forEach((element: any) => {
    element.properties.showNode = true
  })
}
const changeCursor = (bool: boolean) => {
  const element: HTMLElement = document.querySelector('.lf-drag-able') as HTMLElement
  isDrag.value = bool
  if (bool) {
    element.style.cursor = 'default'
    props.lf?.openSelectionSelect()
    props.lf?.extension.selectionSelect.setSelectionSense(true, false)
  } else {
    element.style.cursor = 'pointer'
    props.lf?.closeSelectionSelect()
  }
}
</script>
<style scoped lang="scss">
.is-drag-active {
  background-color: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
}
</style>
