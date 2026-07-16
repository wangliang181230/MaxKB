// 节点选中状态到 Vue 的响应式桥接。
// 节点内容是用 Vue 组件挂进 LogicFlow 的 foreignObject 的，而 LogicFlow 把 isSelected 定义成了 mobx
// observable：Vue 不跟踪 mobx，选中状态变化（框选、点选、多选复制、搜索定位）既不会触发节点组件重渲染，
// LogicFlow 也不会再回调 setHtml，于是出现“多个节点已经选中、能整组拖动，但部分节点没有蓝色边框”的问题——
// 只有恰好因为别的原因重渲染的节点才显示选中样式。
// 这里把模型实例上的 isSelected 访问器包一层，写入时同步更新一个 Vue ref，补上这条响应式链路，
// 同时覆盖 LogicFlow 内部的 setSelected 和项目里直接赋值（含 lodash set）两条写入路径。
import { ref, type Ref } from 'vue'

const SYNCED_KEY = '__lfSelectedSynced'

export function syncNodeSelected(nodeModel: any): Ref<boolean> {
  if (!nodeModel) {
    return ref(false)
  }
  // 同一个模型可能多次挂载组件，已桥接过就直接复用，避免重复包裹访问器
  if (nodeModel[SYNCED_KEY]) {
    return nodeModel[SYNCED_KEY]
  }
  const selected = ref(!!nodeModel.isSelected)
  Object.defineProperty(nodeModel, SYNCED_KEY, {
    value: selected,
    enumerable: false,
    configurable: true,
  })
  const descriptor = Object.getOwnPropertyDescriptor(nodeModel, 'isSelected')
  // 不是实例访问器（非 LogicFlow 标准模型）时退化为挂载时的快照，保持原有行为
  if (!descriptor?.get || !descriptor?.set) {
    return selected
  }
  const rawGet = descriptor.get
  const rawSet = descriptor.set
  Object.defineProperty(nodeModel, 'isSelected', {
    configurable: true,
    enumerable: descriptor.enumerable !== false,
    get() {
      return rawGet.call(this)
    },
    set(value: boolean) {
      const previous = rawGet.call(this)
      rawSet.call(this, value)
      if (previous !== value) {
        selected.value = !!value
      }
    },
  })
  return selected
}
