import { BaseEdgeModel, BaseNodeModel, GraphModel } from '@logicflow/core'
import { defineComponent, h, isVue3, Teleport, markRaw, Fragment, shallowRef } from 'vue-demi'

let active = false
const items: { [key: string]: any } = {}
const renderItems = shallowRef<Array<any>>([])
let syncHandle = 0
const scheduleFrame = (callback: FrameRequestCallback) => {
  if (typeof requestAnimationFrame === 'function') {
    return requestAnimationFrame(callback)
  }
  return setTimeout(() => callback(Date.now()), 0)
}
const cancelFrame = (handle: number) => {
  if (typeof cancelAnimationFrame === 'function') {
    cancelAnimationFrame(handle)
    return
  }
  clearTimeout(handle)
}

function syncItems() {
  syncHandle = 0
  renderItems.value = Object.values(items)
}

function scheduleSyncItems() {
  if (syncHandle) {
    return
  }
  syncHandle = scheduleFrame(syncItems)
}

export function connect(
  id: string,
  component: any,
  container: HTMLDivElement,
  node: BaseNodeModel | BaseEdgeModel,
  graph: GraphModel,
  get_props?: any,
  get_provide?: any,
) {
  if (!get_props) {
    get_props = (node: BaseNodeModel | BaseEdgeModel, graph: GraphModel) => {
      return { nodeModel: node, graph }
    }
  }
  if (!get_provide) {
    get_provide = (node: BaseNodeModel | BaseEdgeModel, graph: GraphModel) => ({
      getNode: () => node,
      getGraph: () => graph,
    })
  }
  if (active) {
    items[id] = markRaw(
      defineComponent({
        render: () => h(Teleport, { to: container } as any, [h(component, get_props(node, graph))]),
        provide: () => get_provide(node, graph),
      }),
    )
    scheduleSyncItems()
  }
}

export function disconnect(id: string) {
  delete items[id]
  scheduleSyncItems()
}
export function disconnectByFlow(flowId: string) {
  Object.keys(items).forEach((key) => {
    if (key.startsWith(flowId)) {
      delete items[key]
    }
  })
  scheduleSyncItems()
}
export function disconnectAll() {
  Object.keys(items).forEach((key) => {
    delete items[key]
  })
  if (syncHandle) {
    cancelFrame(syncHandle)
    syncHandle = 0
  }
  renderItems.value = []
}

export function isActive() {
  return active
}

export function getTeleport(): any {
  if (!isVue3) {
    throw new Error('teleport is only available in Vue3')
  }
  active = true
  syncItems()

  return defineComponent({
    props: {
      flowId: {
        type: String,
        required: true,
      },
    },
    setup() {
      return () => {
        return h(
          Fragment,
          {},
          renderItems.value.map((item) => h(item)),
        )
      }
    },
  })
}
