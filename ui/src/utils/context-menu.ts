// coding=utf-8
// @project: MaxKB
// @file: context-menu.ts
// @desc: 列表卡片右键菜单，让 el-dropdown 在鼠标位置展开

import { nextTick, reactive, ref } from 'vue'

/**
 * 右键卡片或点击“更多”按钮时，把卡片对应的 el-dropdown 锚定到鼠标坐标后展开。
 *
 * 原理：el-dropdown 开启 virtual-triggering 后不会渲染默认插槽，改用 virtual-ref
 * 作为 popper 的参考元素；@popperjs/core 允许参考元素是虚拟元素，只依赖
 * getBoundingClientRect，所以这里用一个响应式对象记录鼠标坐标即可。
 *
 * 用法：
 * 1. 给卡片的 el-dropdown 加上 :virtual-ref="contextMenuAnchor" virtual-triggering
 *    placement="bottom-start" :ref="(d: any) => (cardMenuRefs[item.id] = d)"
 *    （菜单仍写在它的 #dropdown 插槽里，默认插槽不要放任何内容）
 * 2. “更多”按钮改为普通 el-button，点击时 @click.stop="openContextMenu($event, item.id)"
 * 3. 卡片加上 @contextmenu.prevent="openContextMenu($event, item.id)"
 */
export function useContextMenu() {
  const anchor = reactive({
    x: 0,
    y: 0,
    width: 1,
    height: 1,
    top: 0,
    left: 0,
    right: 1,
    bottom: 1,
    getBoundingClientRect() {
      return {
        x: anchor.x,
        y: anchor.y,
        top: anchor.y,
        left: anchor.x,
        right: anchor.x + anchor.width,
        bottom: anchor.y + anchor.height,
        width: anchor.width,
        height: anchor.height,
      }
    },
  })

  const cardMenuRefs = ref<Record<string, any>>({})
  let visibleId = ''

  const open = (id: string) => {
    const dropdown = cardMenuRefs.value[id]
    if (!dropdown) return false
    if (dropdown.handleOpen) dropdown.handleOpen()
    else if (dropdown.show) dropdown.show()
    else dropdown.popperRef?.onOpen?.()
    return true
  }

  const openContextMenu = (e: MouseEvent, id: string) => {
    // 多个卡片共用同一个锚点，切换卡片时先收起上一个
    if (visibleId && visibleId !== id) {
      cardMenuRefs.value[visibleId]?.handleClose?.()
    }
    const x = e.clientX
    const y = e.clientY
    Object.assign(anchor, {
      x,
      y,
      top: y,
      left: x,
      right: x + anchor.width,
      bottom: y + anchor.height,
    })
    visibleId = id
    nextTick(() => {
      // “更多”下拉菜单在卡片 hover 后才创建，实例不存在时下一帧再试一次
      if (!open(id)) {
        nextTick(() => open(id))
      }
    })
  }

  return { contextMenuAnchor: anchor, cardMenuRefs, openContextMenu }
}
