import ReadLongTermMemoryNodeVue from './index.vue'
import { AppNode, AppNodeModel } from '@/workflow/common/app-node'

class ReadLongTermMemoryNode extends AppNode {
  constructor(props: any) {
    super(props, ReadLongTermMemoryNodeVue)
  }
}

export default {
  type: 'read-long-term-memory-node',
  model: AppNodeModel,
  view: ReadLongTermMemoryNode
}
