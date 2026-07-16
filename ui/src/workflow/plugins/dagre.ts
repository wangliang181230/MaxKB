import { DagreLayout, type DagreLayoutOptions } from '@antv/layout'

export default class Dagre {
  static pluginName = 'dagre'
  lf: any
  option: DagreLayoutOptions | any
  render(lf: any) {
    this.lf = lf
  }

  /**
   * option: {
   *   rankdir: "TB", // layout 方向, 可选 TB, BT, LR, RL
   *   align: undefined, // 节点对齐方式，可选 UL, UR, DL, DR
   *   nodeSize: undefined, // 节点大小
   *   nodesepFunc: undefined, // 节点水平间距(px)
   *   ranksepFunc: undefined, // 每一层节点之间间距
   *   nodesep: 40, // 节点水平间距(px) 注意：如果有grid，需要保证nodesep为grid的偶数倍
   *   ranksep: 40, // 每一层节点之间间距 注意：如果有grid，需要保证ranksep为grid的偶数倍
   *   controlPoints: false, // 是否保留布局连线的控制点
   *   radial: false, // 是否基于 dagre 进行辐射布局
   *   focusNode: null, // radial 为 true 时生效，关注的节点
   * };
   */
  layout(option = {}) {
    const { nodes, edges, gridSize } = this.lf.graphModel

    // 为了保证生成的节点在girdSize上，需要处理一下。
    let nodesep = 40
    let ranksep = 40
    if (gridSize > 20) {
      nodesep = gridSize * 2
      ranksep = gridSize * 2
    }

    this.option = {
      type: 'dagre',
      rankdir: 'LR',
      // align: 'UL',
      // align: 'UR',
      align: 'DR',
      nodesep,
      ranksep,
      begin: [120, 120],
      ...option,
    }

    // 分离基础信息节点和布局节点
    const BASE_NODE_TYPES = ['base-node', 'tool-base-node']
    const baseNodes = nodes.filter((n: any) => BASE_NODE_TYPES.includes(n.type))
    const layoutNodes = nodes.filter((n: any) => !BASE_NODE_TYPES.includes(n.type))

    const layoutInstance = new DagreLayout(this.option)
    const layoutData = layoutInstance.layout({
      nodes: layoutNodes.map((node: any) => ({
        id: node.id,
        size: {
          width: node.width,
          height: node.height,
        },
        model: node,
      })),
      edges: edges.map((edge: any) => ({
        source: edge.sourceNodeId,
        target: edge.targetNodeId,
        model: edge,
      })),
    })

    layoutData.nodes?.forEach((node: any) => {
      // @ts-ignore: pass node data
      const { model } = node
      model.set_position({ x: node.x, y: node.y })
    })

    // 应用分支顺序
    this._applyBranchOrdering(layoutNodes, edges)
    // 定位基础节点
    this._positionBaseNodes(baseNodes, layoutNodes)

    this.lf.fitView()
  }

  private _applyBranchOrdering(nodes: any[], edges: any[]) {
    const branchOrderMap = new Map<string, Map<string, number>>()

    for (const node of nodes) {
      const branchList = node.properties?.branch_condition_list
      if (branchList && Array.isArray(branchList) && branchList.length > 0) {
        const orderMap = new Map<string, number>()
        branchList.forEach((b: any, index: number) => {
          orderMap.set(b.id, index)
        })
        branchOrderMap.set(node.id, orderMap)
      }
    }

    if (branchOrderMap.size === 0) return

    const nodeBranchOrder = new Map<string, number>()

    for (const edge of edges) {
      const sourceAnchorId = edge.sourceAnchorId
      if (!sourceAnchorId) continue

      const sourceNodeId = edge.sourceNodeId
      const orderMap = branchOrderMap.get(sourceNodeId)
      if (!orderMap) continue

      const prefix = `${sourceNodeId}_`
      const suffix = '_right'
      if (sourceAnchorId.startsWith(prefix) && sourceAnchorId.endsWith(suffix)) {
        const branchId = sourceAnchorId.slice(prefix.length, -suffix.length)
        const order = orderMap.get(branchId)
        if (order !== undefined) {
          const targetId = edge.targetNodeId
          if (!nodeBranchOrder.has(targetId) || order < nodeBranchOrder.get(targetId)!) {
            nodeBranchOrder.set(targetId, order)
          }
        }
      }
    }

    if (nodeBranchOrder.size === 0) return

    const rankGroups = new Map<number, any[]>()
    for (const node of nodes) {
      const x = Math.round(node.x)
      if (!rankGroups.has(x)) {
        rankGroups.set(x, [])
      }
      rankGroups.get(x)!.push(node)
    }

    for (const [, rankNodes] of rankGroups) {
      if (rankNodes.length < 2) continue

      const branchChildren = rankNodes
        .filter((n) => nodeBranchOrder.has(n.id))
        .sort((a, b) => nodeBranchOrder.get(a.id)! - nodeBranchOrder.get(b.id)!)

      if (branchChildren.length < 2) continue

      const occupiedPositions = branchChildren.map((n) => n.y).sort((a, b) => a - b)

      branchChildren.forEach((node, i) => {
        node.y = occupiedPositions[i]
        node.set_position({ x: node.x, y: occupiedPositions[i] })
      })
    }
  }

  private _positionBaseNodes(baseNodes: any[], layoutNodes: any[]) {
    const startNode = layoutNodes.find((n: any) => n.type === 'start-node' || n.type === 'tool-start-node')
    if (!startNode || baseNodes.length === 0) return

    for (const baseNode of baseNodes) {
      const baseX = startNode.x - (baseNode.width + startNode.width) / 2 - 40
      baseNode.x = baseX
      baseNode.y = startNode.y
      baseNode.set_position({ x: baseX, y: startNode.y })
    }
  }
}
