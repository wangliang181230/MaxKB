import IntentNodeVue from './index.vue'
import { AppNode, AppNodeModel } from '@/workflow/common/app-node'
class IntentNode extends AppNode {
  constructor(props: any) {
    super(props, IntentNodeVue)
  }
}

const get_up_index_height = (branch_list: Array<any>, index: number) => {
    return branch_list
        .filter((item, i) => i < index)
        .map((item) => item.height + 8)
        .reduce((x,y) => x+y, 0)
}

class IntentModel extends AppNodeModel {
    get_width() {
        return 440
    }
    refreshBranch() {
        // 更新节点连接边的path
        this.incoming.edges.forEach((edge: any) => {
            // 调用自定义的更新方案
            edge.updatePathByAnchor()
        })
        this.outgoing.edges.forEach((edge: any) => {
            edge.updatePathByAnchor()
        })
    }
    getDefaultAnchor() {
        const {
            id,
            x,
            y,
            width,
            height,
            properties: { branch_condition_list }
        } = this
        if (this.height === undefined) {
            this.height = 200
        }
        const showNode = this.properties.showNode === undefined ? true : this.properties.showNode
        const anchors: any = []
        anchors.push({
            x: x - width / 2 + 10,
            y: showNode ? y : y - 15,
            id: `${id}_left`,
            edgeAddable: false,
            type: 'left'
        })

        if (branch_condition_list) {
            // 视觉功能区已上移到“输入”下方，其渲染高度会整体抬高右侧分支锚点，
            // 由前端 ResizeObserver 实测写入 properties.vision_height，视觉开/关得到不同偏移
            const FORM_ITEMS_HEIGHT = 543 + (this.properties.vision_height || 0)  // 上方表单占用高度

            for (let index = 0; index < branch_condition_list.length; index++) {
                const element = branch_condition_list[index]

                anchors.push({
                  x: x + width / 2 - 10,
                  y: showNode
                    ? y - height / 2 + FORM_ITEMS_HEIGHT + index * 41.36
                    : y - 15,
                  id: `${id}_${element.id}_right`,
                  type: 'right'
                })
            }
        }
        return anchors
    }
}


export default {
  type: 'intent-node',
  model: IntentModel,
  view: IntentNode
}
