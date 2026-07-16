<template>
  <div
    @mousedown="mousedown"
    class="workflow-node-container p-16"
    style="overflow: visible"
  >
    <div
      class="step-container white-bg border-r-8 p-16"
      :class="{ isSelected: props.nodeModel.isSelected, error: node_status !== 200 }"
      style="overflow: visible"
    >
      <div v-resize="resizeStepContainer">
        <div class="flex-between">
          <div
            class="flex align-center"
            @dragstart.prevent
            @drag.prevent
            @dragover.prevent
            @dragend.prevent
          >
            <component
              :is="iconComponent(`${nodeModel.type}-icon`)"
              class="mr-8"
              :size="24"
              :item="nodeModel?.properties.node_data"
              style="--el-avatar-border-radius: 6px"
            />
            <h4
              class="ellipsis-1 break-all"
              :title="nodeModel.properties.stepName?.length > 8 ? nodeModel.properties.stepName : ''"
              v-html="highlightedStepName(nodeModel.properties.stepName)"
            ></h4>
          </div>

          <div
            @mousemove.stop
            @mousedown.stop
            @keydown.stop
            @click.stop
            style="min-width: 85px; text-align: right"
          >
            <el-button text @click="showNode = !showNode">
              <el-icon class="arrow-icon color-secondary" :class="showNode ? 'rotate-180' : ''"
                ><ArrowDownBold />
              </el-icon>
            </el-button>
            <el-dropdown
              v-if="showConditionOperate(nodeModel.type)"
              :teleported="false"
              trigger="click"
              placement="bottom-start"
            >
              <el-button text>
                <img src="@/assets/workflow/icon_or.svg" alt="" v-if="condition === 'OR'" />
                <img src="@/assets/workflow/icon_and.svg" alt="" v-if="condition === 'AND'" />
              </el-button>
              <template #dropdown>
                <div style="width: 280px" class="p-12-16">
                  <h5>{{ $t('workflow.condition.title') }}</h5>
                  <p class="mt-8 lighter">
                    <span>{{ $t('workflow.condition.front') }}</span>
                    <el-select v-model="condition" size="small" style="width: 60px; margin: 0 8px">
                      <el-option :label="$t('workflow.condition.AND')" value="AND" />
                      <el-option :label="$t('workflow.condition.OR')" value="OR" />
                    </el-select>
                    <span>{{ $t('workflow.condition.text') }}</span>
                  </p>
                </div>
              </template>
            </el-dropdown>
            <el-dropdown v-if="showOperate(nodeModel.type)" :teleported="false" trigger="click">
              <el-button text>
                <AppIcon iconName="app-more" class="color-secondary"></AppIcon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu style="min-width: 144px">
                  <el-dropdown-item @click="renameNode" class="p-8">
                    <AppIcon iconName="app-rename" class="color-secondary"></AppIcon>
                    {{ $t('common.rename') }}</el-dropdown-item
                  >
                  <el-dropdown-item @click="copyNode" class="p-8">
                    <AppIcon iconName="app-copy" class="color-secondary"></AppIcon>
                    {{ $t('common.copy') }}</el-dropdown-item
                  >
                  <template
                    v-if="
                      !(
                        (nodeModel.type == 'tool-lib-node' &&
                          nodeModel['properties'].kind == WorkflowKind.DataSource) ||
                        nodeModel.type == 'data-source-local-node' ||
                        nodeModel.type == 'data-source-web-node'
                      )
                    "
                  >
                    <div class="flex-between p-8" @click.stop>
                      <AppIcon iconName="app-active" class="color-secondary"></AppIcon>
                      <span class="mr-16">{{ $t('common.status.enableStatus') }}</span>
                      <el-switch v-model="nodeEnabled" size="small" /></div
                  ></template>

                  <el-dropdown-item @click="deleteNode" class="border-t p-8">
                    <AppIcon iconName="app-delete" class="color-secondary"></AppIcon>
                    {{ $t('common.delete') }}</el-dropdown-item
                  >
                  <div v-if="sourceName" class="border-t p-8" @click.stop>
                    <div class="color-secondary font-small">{{ $t('common.source') }}</div>
                    <div class="lighter mt-4 break-all">{{ sourceName }}</div>
                  </div>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
        <el-collapse-transition>
          <div @mousedown.stop @keydown.stop @click.stop v-show="showNode" class="mt-16">
            <el-alert
              v-if="nodeDisabled"
              class="mb-16"
              :title="$t('workflow.tip.disabled')"
              type="error"
              show-icon
              :closable="false"
            />
            <el-alert
              v-if="node_status != 200"
              class="mb-16"
              :title="
                props.nodeModel.type === 'application-node'
                  ? $t('workflow.tip.applicationNodeError')
                  : $t('workflow.tip.toolNodeError')
              "
              type="error"
              show-icon
              :closable="false"
            />
            <slot></slot>
            <template v-if="nodeFields.length > 0">
              <div class="flex-between">
                <h5 class="title-decoration-1 mb-8 mt-8">
                  {{ output_title }}
                </h5>
                <div v-if="exceptionNodeList.includes(nodeModel.type)" class="text-right">
                  <span class="mt-8 mr-8 lighter">{{ $t('common.param.exception') }}</span>
                  <el-switch v-model="enable_exception" size="small" />
                </div>
              </div>
              <div class="border-r-6 p-4-12 layout-bg lighter">
                <template v-for="(item, index) in nodeFields" :key="index">
                  <div
                    class="flex-between mb-8 mt-8"
                    @mouseenter="showicon = index"
                    @mouseleave="showicon = null"
                  >
                    <span class="break-all">{{ item.label }} {{ '{' + item.value + '}' }}</span>
                    <el-tooltip
                      effect="dark"
                      :content="$t('workflow.setting.copyParam')"
                      placement="top"
                      v-if="showicon === index"
                    >
                      <el-button link @click="copyClick(item.globeLabel)" style="padding: 0">
                        <AppIcon iconName="app-copy"></AppIcon>
                      </el-button>
                    </el-tooltip>
                  </div>
                </template>
              </div>

              <div class="border-r-6 p-4-12 layout-bg lighter mt-8" v-if="enable_exception">
                <template v-for="(item, index) in abnormalNodeFields" :key="index">
                  <div
                    class="flex-between mb-8 mt-8"
                    @mouseenter="showicon = 'abnormal' + index"
                    @mouseleave="showicon = null"
                  >
                    <span class="break-all">{{ item.label }} {{ '{' + item.value + '}' }}</span>
                    <el-tooltip
                      effect="dark"
                      :content="$t('workflow.setting.copyParam')"
                      placement="top"
                      v-if="showicon === 'abnormal' + index"
                    >
                      <el-button link @click="copyClick(item.globeLabel)" style="padding: 0">
                        <AppIcon iconName="app-copy"></AppIcon>
                      </el-button>
                    </el-tooltip>
                  </div>
                </template>
              </div>
            </template>
          </div>
        </el-collapse-transition>
      </div>
    </div>

    <Teleport to="body">
      <Transition name="dropdown-fade">
        <DropdownMenu
          v-if="showAnchor"
          @mousemove.stop
          @mousedown.stop
          @click.stop
          @wheel="handleWheel"
          :show="showAnchor"
          :inner="true"
          :id="id"
          :style="teleportMenuStyle"
          @clickNodes="clickNodes"
        />
      </Transition>
    </Teleport>

    <el-dialog
      :title="$t('workflow.nodeName')"
      v-model="nodeNameDialogVisible"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :destroy-on-close="true"
      append-to-body
      @submit.prevent
    >
      <el-form label-position="top" ref="titleFormRef" :model="form">
        <el-form-item
          prop="title"
          :rules="[
            {
              required: true,
              message: $t('common.inputPlaceholder'),
              trigger: 'blur',
            },
          ]"
        >
          <el-input v-model="form.title" @blur="form.title = form.title.trim()" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click.prevent="nodeNameDialogVisible = false">
            {{ $t('common.cancel') }}
          </el-button>
          <el-button type="primary" @click="editName(titleFormRef)">
            {{ $t('common.save') }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>
<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { set } from 'lodash'
import { iconComponent } from '../icons/utils'
import { copyClick } from '@/utils/clipboard'
import { WorkflowType, WorkflowKind } from '@/enums/application'
import { MsgError, MsgConfirm } from '@/utils/message'
import type { FormInstance } from 'element-plus'
import { t } from '@/locales'
import { useRoute } from 'vue-router'
import DropdownMenu from '@/components/workflow-dropdown-menu/index.vue'

const route = useRoute()
const {
  params: { id },
} = route as any

const height = ref<{
  stepContainerHeight: number
  inputContainerHeight: number
  outputContainerHeight: number
}>({
  stepContainerHeight: 0,
  inputContainerHeight: 0,
  outputContainerHeight: 0,
})
const showAnchor = ref<boolean>(false)
const anchorData = ref<any>()
const menuPos = ref<{ left: number; top: number } | null>(null)
// 弹出层若留在节点的 foreignObject 内，Firefox 会裁剪溢出区域并丢失其命中测试，
// 导致菜单渲染不全且点不动，只有画布重渲染才恢复；这里把菜单 Teleport 到 body 定位。
// 锚点视口坐标直接用 transformModel.CanvasPointToHtmlPoint 换算（与 getPointByClient 互逆）：
// transformModel 在 graph:transform 触发前已同步更新，而节点 DOM 的新变换要晚一个微任务才绘制，
// 读节点 getBoundingClientRect 会在平移/缩放当帧拿到旧位置，导致菜单不跟随锚点。
const calcMenuPosition = () => {
  const anchor = anchorData.value
  const graphModel = props.nodeModel?.graphModel
  const transformModel = graphModel?.transformModel
  const rootEl = graphModel?.rootEl
  if (!anchor || !transformModel || !rootEl) {
    menuPos.value = null
    return
  }
  const [htmlX, htmlY] = transformModel.CanvasPointToHtmlPoint([anchor.x, anchor.y])
  const rootRect = rootEl.getBoundingClientRect()
  menuPos.value = {
    left: rootRect.left + htmlX,
    top: rootRect.top + htmlY,
  }
}
const teleportMenuStyle = computed(() => {
  const pos = menuPos.value
  if (!pos) {
    return { display: 'none' }
  }
  return {
    position: 'fixed',
    left: pos.left + 14 + 'px',
    top: pos.top + 'px',
    transform: 'translate(0, -50%)',
    right: 'auto',
    zIndex: 2000,
  }
})
const nodeDisabled = computed({
  get: () => {
    return props.nodeModel.properties.disabled || false
  },
  set: (v: boolean) => {
    set(props.nodeModel.properties, 'disabled', v)
  },
})
const nodeEnabled = computed({
  get: () => !nodeDisabled.value,
  set: (v: boolean) => {
    nodeDisabled.value = !v
  },
})
const titleFormRef = ref()
const nodeNameDialogVisible = ref<boolean>(false)
const form = ref<any>({
  title: '',
})

const condition = computed({
  set: (v) => {
    set(props.nodeModel.properties, 'condition', v)
  },
  get: () => {
    if (props.nodeModel.properties.condition) {
      return props.nodeModel.properties.condition
    }
    set(props.nodeModel.properties, 'condition', 'OR')
    return true
  },
})
const showNode = computed({
  set: (v) => {
    set(props.nodeModel.properties, 'showNode', v)
  },
  get: () => {
    if (props.nodeModel.properties.showNode !== undefined) {
      return props.nodeModel.properties.showNode
    }
    set(props.nodeModel.properties, 'showNode', true)
    return true
  },
})

const handleWheel = (event: any) => {
  const isCombinationKeyPressed = event.ctrlKey || event.metaKey
  if (!isCombinationKeyPressed) {
    event.stopPropagation()
  }
}
const node_status = computed(() => {
  if (props.nodeModel.properties.status) {
    return props.nodeModel.properties.status
  }
  return 200
})

const sourceName = computed(() => {
  if (['application-node', 'tool-lib-node'].includes(props.nodeModel.type)) {
    return props.nodeModel.properties.node_data?.name || ''
  }
  return ''
})

function renameNode() {
  form.value.title = props.nodeModel.properties.stepName
  nodeNameDialogVisible.value = true
}
const editName = async (formEl: FormInstance | undefined) => {
  if (!formEl) return
  await formEl.validate((valid) => {
    if (valid) {
      if (
        !props.nodeModel.graphModel.nodes
          .filter((node: any) => node.id !== props.nodeModel.id)
          ?.some((node: any) => node.properties.stepName === form.value.title)
      ) {
        set(props.nodeModel.properties, 'stepName', form.value.title)
        props.nodeModel.clear_next_node_field(true)
        nodeNameDialogVisible.value = false
        formEl.resetFields()
      } else {
        MsgError(t('workflow.tip.repeatedNodeError'))
      }
    }
  })
}

const mousedown = (event?: any) => {
  if (!event?.shiftKey) {
    props.nodeModel.graphModel.clearSelectElements()
  }
  set(props.nodeModel, 'isSelected', !props.nodeModel.isSelected)
  set(props.nodeModel, 'isHovered', !props.nodeModel.isSelected)
  props.nodeModel.graphModel.toFront(props.nodeModel.id)
}
const showicon = ref<number | string | null>(null)
const copyNode = () => {
  props.nodeModel.graphModel.clearSelectElements()
  const cloneNode = props.nodeModel.graphModel.cloneNode(props.nodeModel.id)
  set(cloneNode, 'isSelected', true)
  set(cloneNode, 'isHovered', true)
  props.nodeModel.graphModel.toFront(cloneNode.id)
}
const deleteNode = () => {
  MsgConfirm(t('common.tip'), t('workflow.delete.confirmTitle'), {
    confirmButtonText: t('common.confirm'),
    confirmButtonClass: 'danger',
  }).then(() => {
    if (props.nodeModel.type === WorkflowType.LoopNode) {
      const next = props.nodeModel.graphModel.getNodeOutgoingNode(props.nodeModel.id)
      next.forEach((n: any) => {
        if (n.type === 'loop-body-node') {
          props.nodeModel.graphModel.deleteNode(n.id)
        }
      })
    }
    props.nodeModel.graphModel.deleteNode(props.nodeModel.id)
  })
  props.nodeModel.graphModel.eventCenter.emit('delete_node')
}
const resizeStepContainer = (wh: any) => {
  if (wh.height) {
    if (!props.nodeModel.virtual) {
      if (height.value.stepContainerHeight === wh.height) {
        return
      }
      height.value.stepContainerHeight = wh.height
      props.nodeModel.setHeight(height.value.stepContainerHeight)
    }
  }
}

function clickNodes(item: any) {
  const width = item.properties.width ? item.properties.width : 214
  const nodeModel = props.nodeModel.graphModel.addNode({
    type: item.type,
    properties: item.properties,
    x: anchorData.value?.x + width / 2 + 200,
    y: anchorData.value?.y - item.height,
  })
  props.nodeModel.graphModel.addEdge({
    type: 'app-edge',
    sourceNodeId: props.nodeModel.id,
    sourceAnchorId: anchorData.value?.id,
    targetNodeId: nodeModel.id,
    targetAnchorId: nodeModel.id + '_left',
  })

  closeNodeMenu()
}
const enable_exception = computed({
  set: (v) => {
    set(props.nodeModel.properties, 'enableException', v)
  },
  get: () => {
    if (props.nodeModel.properties.enableException !== undefined) {
      return props.nodeModel.properties.enableException
    }
    set(props.nodeModel.properties, 'enableException', false)
    return false
  },
})
const props = withDefaults(
  defineProps<{
    nodeModel: any
    exceptionNodeList?: string[]
  }>(),
  {
    exceptionNodeList: () => [
      'ai-chat-node',
      'video-understand-node',
      'image-generate-node',
      'image-understand-node',
    ],
  },
)

const nodeFields = computed(() => {
  if (props.nodeModel.properties.config.fields) {
    const fields = props.nodeModel.properties.config.fields?.map((field: any) => {
      return {
        label: field.label,
        value: field.value,
        globeLabel: `{{${props.nodeModel.properties.stepName}.${field.value}}}`,
        globeValue: `{{context['${props.nodeModel.id}'].${field.value}}}`,
      }
    })
    return fields
  }
  return []
})

const output_title = computed(() => {
  return props.nodeModel.properties.config.output_title ?? t('common.param.outputParam')
})

const abnormalNodeFields = computed(() => {
  return [
    {
      label: t('workflow.abnormalInformation'),
      value: 'exception_message',
      globeLabel: `{{${props.nodeModel.properties.stepName}.exception_message}}`,
      globeValue: `{{context['${props.nodeModel.id}'].exception_message}}`,
    },
  ]
})
watch(enable_exception, () => {
  props.nodeModel.graphModel.eventCenter.emit(
    'delete_edge',
    props.nodeModel.outgoing.edges
      .filter((item: any) =>
        [`${props.nodeModel.id}_exception_right`].includes(item.sourceAnchorId),
      )
      .map((item: any) => item.id),
  )
})

function showOperate(type: string) {
  return ![
    WorkflowType.Start,
    WorkflowType.Base,
    WorkflowType.KnowledgeBase,
    WorkflowType.LoopStartNode.toString(),
    WorkflowType.ToolBaseNode,
    WorkflowType.ToolStartNode,
  ].includes(type)
}

function showConditionOperate(type: string) {
  return (
    ![
      WorkflowType.Start,
      WorkflowType.Base,
      WorkflowType.ToolBaseNode,
      WorkflowType.ToolStartNode,
      WorkflowType.KnowledgeBase,
      WorkflowType.LoopStartNode.toString(),
      WorkflowType.DataSourceLocalNode,
      WorkflowType.DataSourceWebNode,
    ].includes(type) && props.nodeModel.properties.kind != WorkflowKind.DataSource
  )
}
// 菜单打开期间平移/缩放会高频触发 graph:transform，用 rAF 合并到每帧最多一次重定位，
// 避免每个 transform 事件都 getBoundingClientRect（与 CanvasPosition 的处理一致）
let repositionRaf = 0
const repositionMenu = () => {
  if (repositionRaf) {
    return
  }
  repositionRaf = window.requestAnimationFrame(() => {
    repositionRaf = 0
    calcMenuPosition()
  })
}
let menuRepositionBound = false
const bindMenuReposition = () => {
  if (menuRepositionBound) {
    return
  }
  menuRepositionBound = true
  props.nodeModel?.graphModel?.eventCenter?.on('graph:transform', repositionMenu)
  window.addEventListener('resize', repositionMenu)
}
const unbindMenuReposition = () => {
  if (repositionRaf) {
    window.cancelAnimationFrame(repositionRaf)
    repositionRaf = 0
  }
  if (!menuRepositionBound) {
    return
  }
  menuRepositionBound = false
  props.nodeModel?.graphModel?.eventCenter?.off('graph:transform', repositionMenu)
  window.removeEventListener('resize', repositionMenu)
}
// 菜单 Teleport 到 body 后脱离了画布，需显式监听“点击外部”才能关闭；
// 菜单自身的 @click.stop 会拦住内部点击，冒泡到这里的都是菜单以外的点击
// 用一次性标志忽略“打开菜单这一次点击”冒泡到 document 的关闭，
// 不依赖 nextTick/事件传播顺序（Preact 下微任务仍会晚于本次 click 到达 document）
let suppressOutsideClick = false
const onDocumentClick = () => {
  if (suppressOutsideClick) {
    return
  }
  closeNodeMenu()
}
let menuOutsideBound = false
const bindOutsideClose = () => {
  if (menuOutsideBound) {
    return
  }
  menuOutsideBound = true
  document.addEventListener('click', onDocumentClick)
}
const unbindOutsideClose = () => {
  if (!menuOutsideBound) {
    return
  }
  menuOutsideBound = false
  document.removeEventListener('click', onDocumentClick)
}
const openNodeMenu = (anchorValue: any) => {
  showAnchor.value = true
  anchorData.value = anchorValue
  calcMenuPosition()
  bindMenuReposition()
  // 同步绑定以捕获后续外部点击；抑制标志在下一个宏任务清除，
  // 恰好跨过“打开这一次点击”冒泡到 document 的阶段
  suppressOutsideClick = true
  bindOutsideClose()
  setTimeout(() => {
    suppressOutsideClick = false
  }, 0)
}
const closeNodeMenu = () => {
  showAnchor.value = false
  anchorData.value = undefined
  suppressOutsideClick = false
  // 不清空 menuPos：保留最后一次定位，让淡出(leave)动画期间菜单仍在原位渐隐，
  // 下次打开会由 calcMenuPosition 重新计算覆盖
  unbindMenuReposition()
  unbindOutsideClose()
}

/**
 * 检索选中时候触发
 * @param kw
 */
const keyWord = ref('')
const currentKeyWord = ref(false)
const selectOn = (kw: string) => {
  keyWord.value = kw
  set(props.nodeModel, 'isSelected', false)
  currentKeyWord.value = false
}
/**
 * 定位时触发
 * @param kw
 */
const focusOn = (kw: string) => {
  props.nodeModel.setSelected(true)
  currentKeyWord.value = true
}
/**
 * 清除时触发
 */
const clearSelectOn = () => {
  keyWord.value = ''
  currentKeyWord.value = false
}

/**
 * 高亮选中关键字
 * @param contentText 需要高亮的内容
 */
const highlightedStepName = (contentText: string) => {
  if (keyWord.value === '') {
    return contentText
  }
  const escaped = keyWord.value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const regex = new RegExp(`(${escaped})`, 'g')
  const color = currentKeyWord.value ? '#FF8800' : '#FFC60A'
  return contentText.replace(regex, `<span style='background: ${color};'>$1</span>`)
}
onMounted(() => {
  set(props.nodeModel, 'openNodeMenu', (anchorData: any) => {
    if (showAnchor.value) {
      closeNodeMenu()
    } else {
      openNodeMenu(anchorData)
    }
  })
  set(props.nodeModel, 'selectOn', selectOn)
  set(props.nodeModel, 'focusOn', focusOn)
  set(props.nodeModel, 'clearSelectOn', clearSelectOn)
})
onBeforeUnmount(() => {
  unbindMenuReposition()
  unbindOutsideClose()
})
</script>
<style lang="scss" scoped>
.workflow-node-container {
  .step-container {
    border: 2px solid #ffffff !important;
    box-sizing: border-box;
    box-shadow: 0px 2px 4px 0px rgba(var(--el-text-color-primary-rgb), 0.12);
    &:hover {
      box-shadow: 0px 6px 24px 0px rgba(var(--el-text-color-primary-rgb), 0.08);
    }
    &.isSelected {
      border: 2px solid var(--el-color-primary) !important;
    }
    &.error {
      border: 1px solid #f54a45 !important;
    }
  }
}
:deep(.el-card) {
  overflow: visible;
}
.app-card {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0px 2px 4px 0px rgba(31, 35, 41, 0.12);
}
.dropdown-fade-enter-active,
.dropdown-fade-leave-active {
  transition:
    opacity 0.2s ease,
    transform 0.2s ease;
}
.dropdown-fade-enter-from,
.dropdown-fade-leave-to {
  opacity: 0;
}
</style>
