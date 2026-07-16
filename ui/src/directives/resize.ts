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

        // observe() 会在下一帧前自动回调一次初始尺寸，且与后续回调同为 contentRect（content-box）口径；
        // 不再手动用 getBoundingClientRect（border-box）补一次，避免首帧两种口径混用触发多余的 resize 回调
        observer.observe(el)

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
