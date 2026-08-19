import type { App } from 'vue'
export default {
  install: (app: App) => {
    app.directive('resize', {
      mounted(el: any, binding: any) {
        let width = 0
        let height = 0
        let frameId = 0
        let pendingSize: null | { width: number; height: number } = null

        const emitSize = (size: { width: number; height: number }) => {
          if (width === size.width && height === size.height) {
            return
          }
          width = size.width
          height = size.height
          binding.value(size)
        }

        const flushSize = () => {
          frameId = 0
          if (!pendingSize) {
            return
          }
          const size = pendingSize
          pendingSize = null
          emitSize(size)
        }

        const scheduleEmit = (size: { width: number; height: number }) => {
          pendingSize = size
          if (!frameId) {
            frameId = window.requestAnimationFrame(flushSize)
          }
        }

        const observer = new ResizeObserver((entries) => {
          const entry = entries[0]
          if (!entry) {
            return
          }
          scheduleEmit({
            width: entry.contentRect.width,
            height: entry.contentRect.height,
          })
        })

        observer.observe(el)
        const rect = el.getBoundingClientRect()
        scheduleEmit({
          width: rect.width,
          height: rect.height,
        })

        ;(el as any).__vueDomResize__ = {
          observer,
          cancel: () => {
            if (frameId) {
              window.cancelAnimationFrame(frameId)
            }
            frameId = 0
            pendingSize = null
          },
        }
      },
      unmounted(el: any) {
        ;(el as any).__vueDomResize__?.cancel?.()
        ;(el as any).__vueDomResize__?.observer?.disconnect?.()
        delete (el as any).__vueDomResize__
      }
    })
  }
}
