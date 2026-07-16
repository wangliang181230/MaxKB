import { cloneDeep } from 'lodash'
import type LogicFlow from '@logicflow/core'
import { type GraphModel } from '@logicflow/core'
import { MsgSuccess, MsgError, MsgConfirm } from '@/utils/message'
import { WorkflowType } from '@/enums/application'
import { t } from '@/locales'
import { copyClick } from '@/utils/clipboard'
import { randomId } from '@/utils/common'
import { getMenuNodes, workflowModelDict } from './data'
let activeCanvasId: string | null = null
type Point = { x: number; y: number }
const lastMouse = {
  x: 0,
  y: 0,
  hasValue: false,
}
let selected: any | null = null
const bindMousePosition = (lf: any) => {
  let frameId = 0
  let pendingMouseEvent: MouseEvent | null = null

  const flushMouse = () => {
    frameId = 0
    if (!pendingMouseEvent) {
      return
    }
    lastMouse.x = pendingMouseEvent.clientX
    lastMouse.y = pendingMouseEvent.clientY
    lastMouse.hasValue = true
    pendingMouseEvent = null
  }

  const updateMouse = (e: MouseEvent) => {
    pendingMouseEvent = e
    if (!frameId) {
      frameId = window.requestAnimationFrame(flushMouse)
    }
  }

  // 推荐直接监听容器，这样鼠标在节点上移动也能拿到
  lf.container.addEventListener('mousemove', updateMouse)

  return () => {
    if (frameId) {
      window.cancelAnimationFrame(frameId)
    }
    lf.container.removeEventListener('mousemove', updateMouse)
  }
}
// LogicFlow 进入选择模式时会把平移范围锁成 [0,0,0,0]（updateTranslateLimits(true)），
// 导致触摸板双指滚动、中键拖拽、适应画布等所有平移能力静默失效。
// 而左键是否平移由画布拖动逻辑单独判断 editConfig.stopMoveGraph，所以这里保持范围始终放开即可，
// 不会因此让左键拖拽变成平移，框选语义保持不变。
const keepTranslateUnlocked = (lf: any) => {
  const transformModel = lf.graphModel?.transformModel
  if (!transformModel || typeof transformModel.updateTranslateLimits !== 'function') {
    return
  }
  const rawUpdateTranslateLimits = transformModel.updateTranslateLimits
  transformModel.updateTranslateLimits = function (limit: any) {
    // 选择模式的锁定(true)改为放开，其他显式配置（vertical/horizontal/自定义范围）保持原样
    return rawUpdateTranslateLimits.call(this, limit === true ? false : limit)
  }
  rawUpdateTranslateLimits.call(transformModel, false)

  return () => {
    transformModel.updateTranslateLimits = rawUpdateTranslateLimits
  }
}

// LogicFlow 的 fitView 只算“内容刚好塞进视口”的比例：节点很少时会把画布放大到百分之一两百（适应之后反而更大），
// 而它算出的比例如果小于画布允许的最小缩放，zoom 会被整体忽略，点适应像是没反应。
// 这里统一成：放得下就不放大、回到原始尺寸；放不下就按“刚好塞下”再乘一个留白系数缩小，并保证不低于允许的最小缩放。
const MAX_FIT_SCALE = 1
const FIT_MARGIN_FACTOR = 0.8

const capFitViewScale = (lf: any) => {
  const graphModel = lf.graphModel
  if (!graphModel || typeof graphModel.getVirtualRectSize !== 'function') {
    return
  }
  const rawFitView = graphModel.fitView

  // 参数与 LogicFlow 保持一致：第一个是纵向留白，第二个是横向留白
  graphModel.fitView = (verticalMargin: number = 20, horizontalMargin: number = 20) => {
    if (!graphModel.nodes?.length) {
      return
    }
    const canvasWidth = graphModel.width || graphModel.rootEl?.clientWidth || 0
    const canvasHeight = graphModel.height || graphModel.rootEl?.clientHeight || 0
    if (canvasWidth <= 0 || canvasHeight <= 0) {
      // 拿不到视口尺寸（容器还没显示等），退回 LogicFlow 原生算法
      return rawFitView.call(graphModel, verticalMargin, horizontalMargin)
    }
    const rect = graphModel.getVirtualRectSize()
    const transformModel = graphModel.transformModel
    const ratioX = (rect.virtualRectWidth + horizontalMargin) / canvasWidth
    const ratioY = (rect.virtualRectHeight + verticalMargin) / canvasHeight
    // 完整塞进视口所需的比例：大于 1 说明节点少、根本不用缩
    const needed = 1 / Math.max(ratioX, ratioY)
    let scale = needed >= 1 ? MAX_FIT_SCALE : needed * FIT_MARGIN_FACTOR
    const miniScale = transformModel.MINI_SCALE_SIZE
    if (typeof miniScale === 'number' && miniScale > 0) {
      // 不能低于允许的最小缩放，否则 LogicFlow 的 zoom 会连位移一起静默忽略
      scale = Math.max(scale, miniScale)
    }
    transformModel.zoom(scale, [canvasWidth / 2, canvasHeight / 2])
    transformModel.focusOn(
      rect.virtualRectCenterPositionX,
      rect.virtualRectCenterPositionY,
      canvasWidth,
      canvasHeight,
    )
  }

  return () => {
    graphModel.fitView = rawFitView
  }
}

// 事件是否属于该画布：落在容器内，且由最内层画布处理（嵌套循环体时避免外层重复响应）
const isCanvasOwnEvent = (container: HTMLElement, target: EventTarget | null) => {
  if (!(target instanceof Element) || !container.contains(target)) return false
  const owner = target.closest('[data-maxkb-lf-canvas]')
  return !owner || owner === container
}

// 从 target 往上到容器，是否存在能顺着滚轮方向继续滚动的元素
const canScrollInDirection = (
  target: Element,
  dx: number,
  dy: number,
  container: HTMLElement,
) => {
  let el: HTMLElement | null =
    target instanceof HTMLElement ? target : (target.parentElement as HTMLElement | null)
  while (el && container.contains(el)) {
    const { overflowX, overflowY } = window.getComputedStyle(el)
    if (dy !== 0 && ['auto', 'scroll', 'overlay'].includes(overflowY)) {
      const max = el.scrollHeight - el.clientHeight
      if (max > 1 && ((dy < 0 && el.scrollTop > 0) || (dy > 0 && el.scrollTop < max))) return true
    }
    if (dx !== 0 && ['auto', 'scroll', 'overlay'].includes(overflowX)) {
      const max = el.scrollWidth - el.clientWidth
      if (max > 1 && ((dx < 0 && el.scrollLeft > 0) || (dx > 0 && el.scrollLeft < max))) return true
    }
    el = el.parentElement
  }
  return false
}

// translate() 的入参是屏幕像素（CanvasPointToHtmlPoint = 画布坐标 * SCALE + TRANSLATE），
// LogicFlow 原生滚轮平移传的是 -delta * SCALE，左键拖拽传的是屏幕增量 1:1，下面两处各自对齐。
// 单次位移上限：按视口尺寸比例取，防止触控板惯性或驱动合成出的异常大 delta 一帧把内容滑出屏幕。
const MAX_WHEEL_VIEW_RATIO = 0.6
// 行模式（Firefox 鼠标滚轮）下一行折算多少像素，让它与 Chrome 的像素模式手感接近
const WHEEL_LINE_PIXEL = 33

const clampDelta = (delta: number, limit: number) => Math.max(-limit, Math.min(limit, delta))

const wheelDeltaToPixels = (delta: number, deltaMode: number, pageSize: number) => {
  if (deltaMode === 1) return delta * WHEEL_LINE_PIXEL
  if (deltaMode === 2) return delta * pageSize
  return delta
}

// 滚轮（触摸板双指）平移画布：节点内的富文本、下拉框等控件普遍绑定了 @wheel 并在非 ctrl 时
// stopPropagation，滚轮传不到画布 svg，鼠标停在它们上方就拖不动。
// 这里在容器捕获阶段接管：控件自身还能沿滚动方向滚时保持原行为，滚到头或本就不可滚动时平移画布。
// 画布空白处也一并接管，因为原生滚轮是逐轴累加、凑满一个网格步长才动一次，斜滑时慢轴会一卡一卡。
const bindWheelPan = (lf: any) => {
  const container = lf.container as HTMLElement
  if (!container) return

  const onWheel = (e: WheelEvent) => {
    // ctrl / ⌘ + 滚轮是缩放，交给已有逻辑
    if (e.ctrlKey || e.metaKey) {
      return
    }
    const target = e.target
    // 嵌套循环体的内层画布整体包在外层的 foreignObject 里，靠归属判断区分，只接管最内层那一只画布
    if (!(target instanceof Element) || !isCanvasOwnEvent(container, target)) {
      return
    }
    if (lf.getEditConfig?.()?.stopScrollGraph) {
      return
    }
    const transformModel = lf.graphModel?.transformModel
    if (!transformModel) {
      return
    }
    const htmlHost = target.closest('foreignObject')
    // 节点 html 内的控件自身还能顺着滚轮方向滚动时保持原行为，不可滚或滚到头的才平移画布
    if (htmlHost && canScrollInDirection(target, e.deltaX, e.deltaY, container)) {
      return
    }
    e.preventDefault()
    // 阻止冒泡到画布 svg，避免与 LogicFlow 自带的滚动平移叠加
    e.stopPropagation()
    const scaleX = transformModel.SCALE_X || 1
    const scaleY = transformModel.SCALE_Y || 1
    const width = container.clientWidth || 0
    const height = container.clientHeight || 0
    // 拿不到视口尺寸时不设上限，避免容器隐藏等场景下完全滚不动
    const limitX = width > 0 ? width * MAX_WHEEL_VIEW_RATIO : Infinity
    const limitY = height > 0 ? height * MAX_WHEEL_VIEW_RATIO : Infinity
    const dx = clampDelta(wheelDeltaToPixels(e.deltaX, e.deltaMode, width), limitX)
    const dy = clampDelta(wheelDeltaToPixels(e.deltaY, e.deltaMode, height), limitY)
    // 与原生滚轮一致按缩放比例折算：缩得越小移动越慢，不会一帧滑出屏幕
    transformModel.translate(-dx * scaleX, -dy * scaleY)
  }

  container.addEventListener('wheel', onWheel, { capture: true, passive: false })

  return () => {
    container.removeEventListener('wheel', onWheel, { capture: true })
  }
}

// 鼠标中键拖拽画布：无论选择模式还是拖拽模式，中键都用于平移画布
const bindMiddleDrag = (lf: any) => {
  const container = lf.container as HTMLElement
  if (!container) return
  let dragging = false
  let selectionClosed = false
  let frameId = 0
  let pendingDragEvent: MouseEvent | null = null
  let lastX = 0
  let lastY = 0
  let restoreDragCursor: (() => void) | null = null

  const flushDrag = () => {
    frameId = 0
    if (!pendingDragEvent) {
      return
    }
    const { clientX, clientY } = pendingDragEvent
    pendingDragEvent = null
    if (!dragging) {
      return
    }
    const transform = lf.graphModel.transformModel
    // translate 入参就是屏幕像素，与 LogicFlow 左键拖拽平移完全一致，内容紧贴手指移动
    transform.translate(clientX - lastX, clientY - lastY)
    lastX = clientX
    lastY = clientY
  }

  const onMouseMove = (e: MouseEvent) => {
    if (!dragging) return
    pendingDragEvent = e
    if (!frameId) {
      frameId = window.requestAnimationFrame(flushDrag)
    }
  }

  const stopDrag = () => {
    dragging = false
    // 松开中键后还原当前模式自身的光标
    restoreDragCursor?.()
    restoreDragCursor = null
    // 恢复中键按下时临时关闭的框选
    if (selectionClosed) {
      lf.extension?.selectionSelect?.open()
      selectionClosed = false
    }
    window.removeEventListener('mousemove', onMouseMove)
    window.removeEventListener('mouseup', stopDrag)
  }

  // 拖拽期间用与拖拽模式一致的手型光标，让中键拖拽有即时反馈
  const applyDragCursor = () => {
    const canvas = container.querySelector<HTMLElement>('.lf-drag-able')
    if (!canvas) return
    const previous = canvas.style.cursor
    canvas.style.cursor = 'pointer'
    restoreDragCursor = () => {
      canvas.style.cursor = previous
    }
  }

  const onMouseDown = (e: MouseEvent) => {
    // 仅响应中键
    if (e.button !== 1) return
    const target = e.target
    if (!isCanvasOwnEvent(container, target)) return
    // 选择模式下临时关闭框选，避免中键拖拽时画出选区矩形
    if (lf.getEditConfig?.()?.stopMoveGraph && lf.extension?.selectionSelect) {
      lf.extension.selectionSelect.close()
      selectionClosed = true
    }
    // 禁止浏览器中键自动滚动等默认行为，保证拖拽流畅
    e.preventDefault()
    applyDragCursor()
    dragging = true
    lastX = e.clientX
    lastY = e.clientY
    window.addEventListener('mousemove', onMouseMove)
    window.addEventListener('mouseup', stopDrag)
  }

  const onAuxClick = (e: MouseEvent) => {
    // 屏蔽中键抬起时的 auxclick，避免触发粘贴等默认行为
    if (e.button === 1) e.preventDefault()
  }

  // 监听捕获阶段，保证早于 LogicFlow 画布自身的 mousedown 处理
  container.addEventListener('mousedown', onMouseDown, true)
  container.addEventListener('auxclick', onAuxClick)

  return () => {
    if (frameId) {
      window.cancelAnimationFrame(frameId)
    }
    frameId = 0
    pendingDragEvent = null
    stopDrag()
    container.removeEventListener('mousedown', onMouseDown, true)
    container.removeEventListener('auxclick', onAuxClick)
  }
}

// 多选后整体拖拽由 LogicFlow 罩在选区上的 .lf-multiple-select 覆盖层驱动，
// 它把鼠标在屏幕上移动的像素直接当作画布坐标增量传给 moveNodes（单节点拖拽走的是另一条已换算过的路径），
// 于是缩放不为 100% 时整组节点的移动距离与鼠标差一个缩放倍数。这里只在该覆盖层拖拽期间补上换算。
const fixMultipleSelectDrag = (lf: any) => {
  const container = lf.container as HTMLElement
  const graphModel = lf.graphModel
  if (!container || !graphModel || typeof graphModel.moveNodes !== 'function') {
    return
  }
  const rawMoveNodes = graphModel.moveNodes
  const doc = container.ownerDocument
  let dragging = false

  const onMouseDown = (e: MouseEvent) => {
    if (e.button !== 0) return
    const overlay = e.target instanceof Element ? e.target.closest('.lf-multiple-select') : null
    // 非覆盖层的按下（单节点、空白处）顺手清掉状态，避免上一轮没收到 mouseup 时残留 true
    if (!overlay || !isCanvasOwnEvent(container, overlay)) {
      dragging = false
      return
    }
    dragging = true
  }

  const endDrag = () => {
    dragging = false
  }

  graphModel.moveNodes = (ids: any, deltaX: number, deltaY: number, keepDistance?: boolean) => {
    if (dragging) {
      const transformModel = graphModel.transformModel
      const scaleX = transformModel?.SCALE_X || 1
      const scaleY = transformModel?.SCALE_Y || 1
      return rawMoveNodes.call(graphModel, ids, deltaX / scaleX, deltaY / scaleY, keepDistance)
    }
    return rawMoveNodes.call(graphModel, ids, deltaX, deltaY, keepDistance)
  }

  // 捕获阶段先于覆盖层自己的 mousedown，且覆盖层会 stopPropagation，节点不会被同时拖动
  container.addEventListener('mousedown', onMouseDown, true)
  // mouseup 跟 LogicFlow 的拖拽一致监听从 document 冒泡，另外补上 blur：鼠标在窗口外松开时也能清除状态
  doc.addEventListener('mouseup', endDrag)
  window.addEventListener('blur', endDrag)

  return () => {
    graphModel.moveNodes = rawMoveNodes
    dragging = false
    container.removeEventListener('mousedown', onMouseDown, true)
    doc.removeEventListener('mouseup', endDrag)
    window.removeEventListener('blur', endDrag)
  }
}

// 触摸板双指横滑会被浏览器当成“后退/前进”手势（Chrome/Edge 的 overscroll 导航、Safari 的 swipe back），
// 该手势由根滚动器决定，写在画布元素上无效（工作流页面自己并不横向滚动），只能暂时关掉 html/body 的横向 overscroll 默认行为。
// 用引用计数：多个工作流画布同时挂载时，内层卸载不能把外层的防护也去掉。
const OVERSCROLL_NAV_CLASS = 'workflow-no-overscroll-nav'
let overscrollNavGuard = 0

export const blockOverscrollNavigation = () => {
  if (overscrollNavGuard++ === 0) {
    document.documentElement.classList.add(OVERSCROLL_NAV_CLASS)
  }
  // 幂等释放：重复调用不会把计数多扣一层，把其他画布的防护一起关掉
  let released = false

  return () => {
    if (released) {
      return
    }
    released = true
    if (--overscrollNavGuard <= 0) {
      overscrollNavGuard = 0
      document.documentElement.classList.remove(OVERSCROLL_NAV_CLASS)
    }
  }
}

const bindCanvasActive = (lf: any) => {
  const container = lf.container as HTMLElement
  if (!container) return

  // 让容器可聚焦
  container.tabIndex = 0
  // 标记 LogicFlow 画布容器，供快捷键处理区分嵌套画布
  container.dataset.maxkbLfCanvas = 'true'

  const activate = () => {
    activeCanvasId = lf.graphModel.flowId
    container.focus()
  }

  container.addEventListener('mousedown', activate)
  container.addEventListener('focus', activate)

  return () => {
    container.removeEventListener('mousedown', activate)
    container.removeEventListener('focus', activate)
  }
}
function translationNodeData(nodeData: any, distance: any) {
  nodeData.x += distance
  nodeData.y += distance
  if (nodeData.text) {
    nodeData.text.x += distance
    nodeData.text.y += distance
  }
  return nodeData
}

function translationEdgeData(edgeData: any, distance: any) {
  if (edgeData.startPoint) {
    edgeData.startPoint.x += distance
    edgeData.startPoint.y += distance
  }
  if (edgeData.endPoint) {
    edgeData.endPoint.x += distance
    edgeData.endPoint.y += distance
  }
  if (edgeData.pointsList && edgeData.pointsList.length > 0) {
    edgeData.pointsList.forEach((point: any) => {
      point.x += distance
      point.y += distance
    })
  }
  if (edgeData.text) {
    edgeData.text.x += distance
    edgeData.text.y += distance
  }
  return edgeData
}

const TRANSLATION_DISTANCE = 40
let CHILDREN_TRANSLATION_DISTANCE = 40

export function initDefaultShortcut(lf: LogicFlow, graph: GraphModel) {
  const removeMousePosition = bindMousePosition(lf)
  const removeCanvasActive = bindCanvasActive(lf)
  const removeMiddleDrag = bindMiddleDrag(lf)
  const removeWheelPan = bindWheelPan(lf)
  const removeTranslateLock = keepTranslateUnlocked(lf)
  const removeFitViewCap = capFitViewScale(lf)
  const removeMultiDragFix = fixMultipleSelectDrag(lf)
  const { keyboard } = lf
  const {
    options: { keyboard: keyboardOptions },
  } = keyboard
  const copy_node = () => {
    CHILDREN_TRANSLATION_DISTANCE = TRANSLATION_DISTANCE
    if (!keyboardOptions?.enabled) return true
    if (graph.textEditElement) return true
    const { guards } = lf.options
    const elements = graph.getSelectElements(false)
    const enabledClone = guards && guards.beforeClone ? guards.beforeClone(elements) : true
    if (!enabledClone || (elements.nodes.length === 0 && elements.edges.length === 0)) {
      selected = null
      return true
    }
    const base_nodes = elements.nodes.filter(
      (node: any) => node.type === WorkflowType.Start || node.type === WorkflowType.Base,
    )
    if (base_nodes.length > 0) {
      MsgError(base_nodes[0]?.properties?.stepName + t('workflow.tip.cannotCopy'))
      return
    }
    selected = cloneDeep(elements)
    selected.nodes.forEach((node: any) => translationNodeData(node, TRANSLATION_DISTANCE))
    selected.edges.forEach((edge: any) => translationEdgeData(edge, TRANSLATION_DISTANCE))
    copyClick(JSON.stringify(selected))
    return false
  }
  // 3. 求节点包围盒
  const getBounds = (nodes: any[]) => {
    if (!nodes.length) {
      return { minX: 0, maxX: 0, minY: 0, maxY: 0 }
    }

    let minX = nodes[0].x
    let maxX = nodes[0].x
    let minY = nodes[0].y
    let maxY = nodes[0].y

    for (const node of nodes) {
      if (node.x < minX) minX = node.x
      if (node.x > maxX) maxX = node.x
      if (node.y < minY) minY = node.y
      if (node.y > maxY) maxY = node.y
    }

    return { minX, maxX, minY, maxY }
  }

  // 4. 整体平移
  const moveData = (data: any, dx: number, dy: number) => {
    for (const node of data.nodes ?? []) {
      node.x += dx
      node.y += dy
    }

    for (const edge of data.edges ?? []) {
      if (edge.startPoint) {
        edge.startPoint.x += dx
        edge.startPoint.y += dy
      }
      if (edge.endPoint) {
        edge.endPoint.x += dx
        edge.endPoint.y += dy
      }
      if (edge.text && typeof edge.text.x === 'number' && typeof edge.text.y === 'number') {
        edge.text.x += dx
        edge.text.y += dy
      }
      if (Array.isArray(edge.pointsList)) {
        edge.pointsList = edge.pointsList.map((p: Point) => ({
          ...p,
          x: p.x + dx,
          y: p.y + dy,
        }))
      }
    }
  }
  const resetData = (data: any) => {
    const idMap = new Map<string, string>()

    const getOrCreateId = (oldId: string) => {
      let newId = idMap.get(oldId)
      if (!newId) {
        newId = randomId()
        idMap.set(oldId, newId)
      }
      return newId
    }

    for (const node of data.nodes) {
      node.id = getOrCreateId(node.id)
    }

    for (const edge of data.edges) {
      const oldEdgeId = edge.id
      const oldSourceNodeId = edge.sourceNodeId
      const oldTargetNodeId = edge.targetNodeId

      edge.id = getOrCreateId(oldEdgeId)
      edge.sourceNodeId = getOrCreateId(oldSourceNodeId)
      edge.targetNodeId = getOrCreateId(oldTargetNodeId)

      if (typeof edge.sourceAnchorId === 'string') {
        edge.sourceAnchorId = edge.sourceAnchorId.replace(oldSourceNodeId, edge.sourceNodeId)
      }

      if (typeof edge.targetAnchorId === 'string') {
        edge.targetAnchorId = edge.targetAnchorId.replace(oldTargetNodeId, edge.targetNodeId)
      }
    }

    return data
  }

  const paste_node = async (e: ClipboardEvent) => {
    if (lf.graphModel.flowId !== activeCanvasId) {
      return true
    }
    if (!keyboardOptions?.enabled) return true
    if (graph.textEditElement) return true
    const text = e.clipboardData?.getData('text/plain') || ''
    const data = parseAndValidate(text)
    selected = resetData(data)
    const workflowMode = lf.graphModel.get_provide(null, null).workflowMode
    const menus = getMenuNodes(workflowMode)
    const nodes = menus?.flatMap((m: any) => m.list).map((n) => n.type)

    if (selected && (selected.nodes || selected.edges)) {
      if (!lastMouse.hasValue) {
        moveData(data, 40, 40)
      } else {
        // LogicFlow 文档里 getPointByClient 会把页面坐标转成画布坐标
        const point = lf.graphModel.getPointByClient({
          x: lastMouse.x,
          y: lastMouse.y,
        })
        const mouseCanvasX = point.canvasOverlayPosition.x
        const mouseCanvasY = point.canvasOverlayPosition.y

        const { minX, maxX, minY, maxY } = getBounds(selected.nodes)
        const centerX = (minX + maxX) / 2
        const centerY = (minY + maxY) / 2
        moveData(data, mouseCanvasX - centerX, mouseCanvasY - centerY)
      }

      selected.nodes = selected.nodes.filter(
        (n: any) => nodes?.includes(n.type) || workflowModelDict[workflowMode](n),
      )
      lf.clearSelectElements()
      const addElements = lf.addElements(selected, CHILDREN_TRANSLATION_DISTANCE)
      if (!addElements) return true
      addElements.nodes.forEach((node) => lf.selectElementById(node.id, true))
      addElements.edges.forEach((edge) => lf.selectElementById(edge.id, true))
      selected.nodes.forEach((node: any) => translationNodeData(node, TRANSLATION_DISTANCE))
      selected.edges.forEach((edge: any) => translationEdgeData(edge, TRANSLATION_DISTANCE))
      CHILDREN_TRANSLATION_DISTANCE = CHILDREN_TRANSLATION_DISTANCE + TRANSLATION_DISTANCE
    }
    selected = undefined
    return false
  }

  const parseAndValidate = (text: string) => {
    let data: any
    try {
      data = JSON.parse(text)
    } catch {
      throw new Error('数据不是合法的 JSON')
    }

    if (!data || typeof data !== 'object' || Array.isArray(data)) {
      throw new Error('数据必须是对象')
    }

    if (!('nodes' in data)) {
      throw new Error('数据缺少 nodes 字段')
    }

    if (!('edges' in data)) {
      throw new Error('数据缺少 edges 字段')
    }

    if (!Array.isArray(data.nodes)) {
      throw new Error('nodes 必须是数组')
    }

    for (let i = 0; i < data.nodes.length; i++) {
      const node = data.nodes[i]

      if (!node || typeof node !== 'object' || Array.isArray(node)) {
        throw new Error(`nodes[${i}] 必须是对象`)
      }

      if (!('id' in node) || node.id === undefined || node.id === null || node.id === '') {
        throw new Error(`nodes[${i}] 缺少 id`)
      }
    }

    return data
  }
  document.addEventListener('paste', paste_node)

  const delete_node = () => {
    const elements = graph.getSelectElements(true)
    lf.clearSelectElements()
    if (elements.nodes.length == 0 && elements.edges.length == 0) {
      return
    }
    if (elements.edges.length > 0 && elements.nodes.length == 0) {
      elements.edges
        .filter((edge) => !['loop-edge'].includes(edge.type || ''))
        .forEach((edge: any) => lf.deleteEdge(edge.id))
      return
    }
    const nodes = elements.nodes.filter((node) =>
      [
        'start-node',
        'tool-start-node',
        'tool-base-node',
        'base-node',
        'loop-body-node',
        'loop-start-node',
        'knowledge-base-node',
      ].includes(node.type),
    )
    if (nodes.length > 0) {
      MsgError(`${nodes[0].properties?.stepName}${t('workflow.delete.deleteMessage')}`)
      return
    }
    MsgConfirm(t('common.tip'), t('workflow.delete.confirmTitle'), {
      confirmButtonText: t('common.confirm'),
      confirmButtonClass: 'danger',
    }).then(() => {
      if (!keyboardOptions?.enabled) return true
      if (graph.textEditElement) return true

      elements.edges.forEach((edge: any) => lf.deleteEdge(edge.id))
      elements.nodes.forEach((node: any) => {
        if (node.type === 'loop-node') {
          const next = lf.getNodeOutgoingNode(node.id)
          next.forEach((n: any) => {
            if (n.type === 'loop-body-node') {
              lf.deleteNode(n.id)
            }
          })
        }
        lf.deleteNode(node.id)
      })
    })

    return false
  }
  graph.eventCenter.on('copy_node', copy_node)
  // 复制
  keyboard.on(['cmd + c', 'ctrl + c'], copy_node)
  // 粘贴
  keyboard.on(['cmd + v', 'ctrl + v'], () => {})
  // 切换模式：选择模式/拖拽模式（使用原生 keydown，避免 LogicFlow keyboard 对单字符键的兼容问题）
  const container = lf.container as HTMLElement
  const isEditableTarget = (target: EventTarget | null) => {
    if (!(target instanceof Element)) return false
    if (target === document.body) return false
    return target.closest('input, textarea, [contenteditable]') !== null
  }
  const toggleSelectionMode = (e: KeyboardEvent) => {
    if (e.key !== 'v' && e.key !== 'V') return
    if (e.ctrlKey || e.metaKey || e.altKey) return
    if (!keyboardOptions?.enabled) return
    if (graph.textEditElement) return
    // 监听在 document 上，避免画布未聚焦时首次按 V 不生效；输入控件聚焦时不响应
    if (isEditableTarget(e.target)) return
    // 循环体内层画布不单独处理：光标状态与工具栏按钮都属于外层画布
    if (container.parentElement?.closest('[data-maxkb-lf-canvas]')) return
    const targetCanvas =
      e.target instanceof Element
        ? (e.target.closest('[data-maxkb-lf-canvas]') as HTMLElement | null)
        : null
    if (targetCanvas) {
      // 事件属于其他独立画布时，不由当前画布处理
      if (!container.contains(targetCanvas)) return
    } else if (e.target !== document.body && e.target !== document.documentElement) {
      // 焦点在画布之外（弹窗、侧边面板等），不响应快捷键
      return
    } else if (activeCanvasId && activeCanvasId !== lf.graphModel.flowId) {
      // 已有其他画布激活时，不由当前画布处理
      return
    }
    const element: HTMLElement = document.querySelector('.lf-drag-able') as HTMLElement
    // 初始内联 cursor 为空（拖拽模式），不能把非 pointer 误判为选择模式，否则首次按 V 无效果
    const isSelectionMode = element?.style.cursor === 'default'
    if (isSelectionMode) {
      lf.closeSelectionSelect()
      if (element) element.style.cursor = 'pointer'
      graph.eventCenter.emit('selection:mode:change', false as any)
    } else {
      lf.openSelectionSelect()
      lf.extension.selectionSelect.setSelectionSense(true, false)
      if (element) element.style.cursor = 'default'
      graph.eventCenter.emit('selection:mode:change', true as any)
    }
  }
  document.addEventListener('keydown', toggleSelectionMode)
  // undo
  keyboard.on(['cmd + z', 'ctrl + z'], () => {
    // if (!keyboardOptions?.enabled) return true
    // if (graph.textEditElement) return true
    // lf.undo()
    // return false
  })
  // redo
  keyboard.on(['cmd + y', 'ctrl + y'], () => {
    if (!keyboardOptions?.enabled) return true
    if (graph.textEditElement) return true
    lf.redo()
    return false
  })
  // delete
  keyboard.on(['backspace'], delete_node)

  return () => {
    document.removeEventListener('paste', paste_node)
    document.removeEventListener('keydown', toggleSelectionMode)
    removeMousePosition()
    removeCanvasActive?.()
    removeMiddleDrag?.()
    removeWheelPan?.()
    removeTranslateLock?.()
    removeFitViewCap?.()
    removeMultiDragFix?.()
    if (activeCanvasId === lf.graphModel.flowId) {
      activeCanvasId = null
    }
  }
}
