// 边-锚点连接索引：把“某锚点是否已连线”的判断从每次渲染 O(边数) 的全表扫描降为 O(1) 查询。
// 锚点图标在 hover、拖拽节点、整图渲染时高频重绘，原来每个锚点都 graphModel.edges.some(...) 扫一遍，
// 大图下是 O(锚点数 × 边数)。这里维护一个“被任意边引用到的锚点 id”集合，只在边的绑定关系变化时重建，
// 拖拽/缩放/hover 期间命中缓存、零重建。
// 左锚点只会作为 targetAnchorId、右锚点只会作为 sourceAnchorId，两侧合并进同一个 Set 即可正确回答“是否已连线”。

type IndexEntry = {
  set: Set<string> | null
  len: number
  dirty: boolean
}

// 以 graphModel 为键，随画布实例回收自动释放，无需手动清理内存
const cache = new WeakMap<object, IndexEntry>()

// 会改变边的锚点绑定关系的事件：增边、删边、重连、调整、删节点连带删边、撤销/重做、整图重渲染。
// 另外 isAnchorConnected 里还会用 edges.length 兜底，即便漏掉某个增删事件也不会读到过期集合。
const MUTATION_EVENTS = [
  'edge:add',
  'edge:delete',
  'edge:exchange-node',
  'edge:adjust',
  'node:delete',
  'history:change',
  'graph:rendered',
]

const getEntry = (graphModel: any): IndexEntry => {
  let entry = cache.get(graphModel)
  if (!entry) {
    entry = { set: null, len: -1, dirty: true }
    cache.set(graphModel, entry)
  }
  return entry
}

const rebuild = (graphModel: any, entry: IndexEntry) => {
  const set = new Set<string>()
  const edges = graphModel.edges || []
  for (const edge of edges) {
    if (edge.sourceAnchorId) set.add(edge.sourceAnchorId)
    if (edge.targetAnchorId) set.add(edge.targetAnchorId)
  }
  entry.set = set
  entry.len = edges.length
  entry.dirty = false
}

// O(1) 判断锚点是否已连线：命中缓存直接查 Set；仅当被事件标脏或边数量变化时才 O(边数) 重建。
export const isAnchorConnected = (graphModel: any, anchorId: string): boolean => {
  if (!graphModel || !anchorId) {
    return false
  }
  const entry = getEntry(graphModel)
  const edges = graphModel.edges || []
  if (entry.dirty || entry.set === null || entry.len !== edges.length) {
    rebuild(graphModel, entry)
  }
  return entry.set!.has(anchorId)
}

// 订阅边绑定变更事件把缓存标脏，返回解绑函数。每个画布（含循环体内层）各自安装、各自清理。
export const installEdgeAnchorIndex = (graphModel: any) => {
  const eventCenter = graphModel?.eventCenter
  if (!eventCenter) {
    return
  }
  const entry = getEntry(graphModel)
  const markDirty = () => {
    entry.dirty = true
  }
  MUTATION_EVENTS.forEach((evt) => eventCenter.on(evt, markDirty))
  return () => {
    MUTATION_EVENTS.forEach((evt) => eventCenter.off(evt, markDirty))
    cache.delete(graphModel)
  }
}
