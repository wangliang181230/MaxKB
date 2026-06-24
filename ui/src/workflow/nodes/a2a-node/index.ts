import A2ANodeVue from './index.vue'
import { AppNode, AppNodeModel } from '@/workflow/common/app-node'

class A2ANode extends AppNode {
  constructor(props: any) {
    super(props, A2ANodeVue)
  }
}

export default {
  type: 'a2a-node',
  model: AppNodeModel,
  view: A2ANode
}
