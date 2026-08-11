// coding=utf-8
//
// @desc: 工作流分支拖拽排序的公共逻辑。
//        判断器(condition)、Switch(switch)、意图识别(intent) 三类节点的分支都带有右侧锚点，
//        拖拽排序时需要让“整条分支（标题 + 内容 + 锚点/连线）”一起移动，故抽取为公共方法复用。
import { cloneDeep, set } from 'lodash'

/**
 * 拖拽过滤选择器：整行标题作为拖拽手柄时，落在这些交互控件（删除按钮、下拉框、输入框等）
 * 上的按下不触发拖拽，避免误拖拽并保证控件正常交互。
 * 注意：使用本选择器的 VueDraggable 必须同时设置 :prevent-on-filter="false"，
 * 否则 Sortable 会对命中的 mousedown 调用 preventDefault()，导致输入框无法获得焦点。
 */
export const BRANCH_DRAG_IGNORE_SELECTOR =
  '.el-button, .el-select, .el-input, .el-cascader, .el-input-number, .el-switch, input, textarea, button'

/**
 * 依据分支当前顺序重建 branch_condition_list（保留每个分支 id 对应的高度），
 * 并刷新连线，使右侧锚点随分支一起移动。
 * @param nodeModel 节点模型
 * @param branch    排序后的分支列表
 */
export function syncBranchAnchorOrder(nodeModel: any, branch: Array<any>) {
  const branch_condition_list = cloneDeep(
    nodeModel.properties.branch_condition_list ? nodeModel.properties.branch_condition_list : [],
  )
  const new_branch_condition_list = branch.map((item: any, index: number) => {
    const exist = branch_condition_list.find((b: any) => b.id === item.id)
    return { index: index, height: exist ? exist.height : 12, id: item.id }
  })
  set(nodeModel.properties, 'branch_condition_list', new_branch_condition_list)
  nodeModel.refreshBranch()
}

/**
 * 拖拽排序：整条分支（标题 + 内容 + 锚点）一起移动，并同步刷新锚点位置。
 * 末尾的兜底分支（判断器的 ELSE、Switch 的 DEFAULT、意图识别的“其他”）不可被移动或被跨越。
 * @param nodeModel    节点模型
 * @param oldIndex     拖拽起始下标
 * @param newIndex     拖拽目标下标
 * @param lockedTail   末尾锁定分支数量，默认 1
 * @param relabel      可选：排序后按位置重新生成标题（如 IF / ELSE IF N、CASE N）
 */
export function reorderBranchWithAnchor(
  nodeModel: any,
  oldIndex: number | undefined,
  newIndex: number | undefined,
  lockedTail: number = 1,
  relabel?: (branch: Array<any>) => void,
) {
  if (oldIndex === undefined || newIndex === undefined || oldIndex === newIndex) return
  const branch: Array<any> = cloneDeep(nodeModel.properties.node_data.branch)
  const movableEnd = branch.length - lockedTail
  // 起始或目标落在锁定的兜底分支上则不允许排序
  if (oldIndex >= movableEnd || newIndex >= movableEnd) return
  const [moved] = branch.splice(oldIndex, 1)
  branch.splice(newIndex, 0, moved)
  relabel?.(branch)
  set(nodeModel.properties.node_data, 'branch', branch)
  syncBranchAnchorOrder(nodeModel, branch)
}
