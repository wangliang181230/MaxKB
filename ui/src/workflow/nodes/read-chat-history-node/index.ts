import ReadChatHistoryNodeVue from './index.vue'
import { AppNode, AppNodeModel } from '@/workflow/common/app-node'

class ReadChatHistoryNode extends AppNode {
  constructor(props: any) {
    super(props, ReadChatHistoryNodeVue)
  }
}

export default {
  type: 'read-chat-history-node',
  model: AppNodeModel,
  view: ReadChatHistoryNode
}
