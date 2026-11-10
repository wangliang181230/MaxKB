<template>
  <div class="provider-list">
    <el-scrollbar>
      <div class="p-8">
        <div v-if="showShared && hasPermission(EditionConst.IS_EE, 'OR')" class="border-b mb-4">
          <div
            @click="handleSharedNodeClick"
            class="shared-button flex cursor"
            :class="active?.provider === 'share' && 'active'"
          >
            <AppIcon
              iconName="app-shared-active"
              style="font-size: 18px"
              class="color-primary"
            ></AppIcon>
            <span class="ml-8">{{ $t('views.shared.shared_model') }}</span>
          </div>
        </div>
        <div
          class="all-mode flex cursor"
          @click="clickListHandle(allObj as Provider)"
          :class="!active?.provider ? 'all-mode-active color-primary-1' : ''"
        >
          <AppIcon
            class="mr-8 color-primary"
            style="height: 20px; width: 20px"
            :iconName="'app-all-menu-active'"
          ></AppIcon>
          <span>{{ $t('views.model.modelType.allModel') }}</span>
        </div>

        <el-collapse v-model="activeNames" class="model-collapse" expand-icon-position="left">
          <el-collapse-item
            :title="$t('views.model.modelType.publicModel')"
            name="1"
            icon="CaretRight"
          >
            <template #title>
              <div class="flex align-center">
                <AppIcon iconName="app-folder" style="font-size: 20px"></AppIcon>
                <span class="ml-8">
                  {{ $t('views.model.modelType.publicModel') }}
                </span>
              </div>
            </template>
            <common-list
              :data="online_provider_list"
              v-loading="loading"
              @click="clickListHandle"
              value-key="provider"
              default-active=""
              ref="commonList1"
            >
              <template #default="{ row }">
                <div class="flex align-center">
                  <span
                    :innerHTML="row.icon"
                    alt=""
                    style="height: 20px; width: 20px"
                    class="mr-8"
                  />
                  <span class="ellipsis-1" :title="getProviderDisplayName(row)">
                    {{ row.name }}
                    <span v-if="row.model_count !== undefined" class="model-count">
                      ({{ row.model_count }})
                    </span>
                  </span>
                </div>
              </template>
            </common-list>
          </el-collapse-item>
          <el-collapse-item
            :title="$t('views.model.modelType.privateModel')"
            name="2"
            icon="CaretRight"
          >
            <template #title>
              <div class="flex align-center">
                <AppIcon iconName="app-folder" style="font-size: 20px"></AppIcon>
                <span class="ml-8">
                  {{ $t('views.model.modelType.privateModel') }}
                </span>
              </div>
            </template>
            <common-list
              :data="local_provider_list"
              v-loading="loading"
              @click="clickListHandle"
              value-key="provider"
              default-active=""
              ref="commonList2"
            >
              <template #default="{ row }">
                <div class="flex align-center">
                  <span
                    :innerHTML="row.icon"
                    alt=""
                    style="height: 20px; width: 20px"
                    class="mr-8"
                  />
                  <span class="ellipsis-1" :title="getProviderDisplayName(row)">
                    {{ row.name }}
                    <span v-if="row.model_count !== undefined" class="model-count">
                      ({{ row.model_count }})
                    </span>
                  </span>
                </div>
              </template>
            </common-list>
          </el-collapse-item>
        </el-collapse>
      </div>
    </el-scrollbar>
  </div>
</template>
<script lang="ts" setup>
import { watch, ref } from 'vue'
import type { Provider, Model } from '@/api/type/model'
import { modelTypeList, allObj } from '@/views/model/component/data'
import { EditionConst } from '@/utils/permission/data'
import { hasPermission } from '@/utils/permission/index'
import { t } from '@/locales'
const props = defineProps<{
  data: Array<Provider>
  loading: boolean
  showShared?: boolean
  active?: Provider
}>()
const emit = defineEmits(['click'])

const online_provider_list = ref<Array<Provider>>([])
const local_provider_list = ref<Array<Provider>>([])
// 公有模型与私有模型目录默认展开
const activeNames = ref<Array<string>>(['1', '2'])

const getProviderDisplayName = (row: Provider) => {
  return row.model_count === undefined ? row.name : `${row.name} (${row.model_count})`
}

watch(
  () => props.data,
  (list) => {
    online_provider_list.value = []
    local_provider_list.value = []
    // 私有供应商展示顺序：本地模型 > vLLM > Ollama > Docker AI > Xorbits Inference > 其它
    const local_provider = [
      'model_local_provider',
      'model_vllm_provider',
      'model_ollama_provider',
      'model_docker_ai_provider',
      'model_xinference_provider',
    ]
    const domestic_provider = [
      'model_volcanic_engine_provider',
      'aliyun_bai_lian_model_provider',
      'model_deepseek_provider',
      'model_kimi_provider',
      'model_minimax_provider',
      'model_siliconCloud_provider',
      'model_tencent_provider',
      'model_wenxin_provider',
      'model_xf_provider',
      'model_zhipu_provider',
    ]
    // 火山引擎 > 阿里云百炼 > DeepSeek > OpenAI > 其余国产厂商 > 海外厂商；同组内按 provider 字母序
    const pinned_provider = [
      'model_volcanic_engine_provider',
      'aliyun_bai_lian_model_provider',
      'model_deepseek_provider',
      'model_openai_provider',
    ]
    const providerPriority = (provider: string) => {
      const pinnedIndex = pinned_provider.indexOf(provider)
      if (pinnedIndex > -1) return pinnedIndex
      if (domestic_provider.indexOf(provider) > -1) return pinned_provider.length
      return pinned_provider.length + 1
    }
    list
      .filter((v) => v.provider)
      ?.forEach((item) => {
        if (local_provider.indexOf(item.provider) > -1) {
          local_provider_list.value.push(item)
        } else {
          online_provider_list.value.push(item)
        }
      })
    online_provider_list.value.sort((a, b) => {
      const pa = providerPriority(a.provider)
      const pb = providerPriority(b.provider)
      return pa !== pb ? pa - pb : a.provider.localeCompare(b.provider)
    })
    local_provider_list.value.sort((a, b) => {
      const pa = local_provider.indexOf(a.provider)
      const pb = local_provider.indexOf(b.provider)
      return pa - pb
    })
  },
  { immediate: true },
)

const clickListHandle = (item: Provider) => {
  emit('click', item)
}

const handleSharedNodeClick = () => {
  emit('click', { provider: 'share', name: t('views.shared.shared_model') })
}
</script>
<style lang="scss" scoped>
.provider-list {
  height: calc(var(--app-main-height));
  .model-count {
    color: var(--el-text-color-secondary);
  }
  .all-mode {
    padding: 10px 8px;
    font-weight: 400;
    &:hover {
      border-radius: var(--app-border-radius-small);
      background: rgba(var(--el-text-color-primary-rgb), 0.1);
    }
  }
  .all-mode-active {
    border-radius: var(--app-border-radius-small);
    color: var(--el-color-primary);
    font-weight: 500 !important;
    background: var(--el-color-primary-light-9);
    &:hover {
      background: var(--el-color-primary-light-9);
    }
  }
  .model-collapse {
    border-top: none !important;
    border-bottom: none !important;
    :deep(.el-collapse-item__header) {
      border-bottom: none !important;
      padding-left: 8px;
      font-size: 14px;
      font-weight: 400;
      height: 40px;
      background: none;
      &:hover {
        background: rgba(var(--el-text-color-primary-rgb), 0.1);
        border-radius: var(--app-border-radius-small);
      }
    }
    :deep(.el-collapse-item) {
      margin-top: 2px;
    }
    :deep(.common-list) {
      li {
        padding-left: 50px !important;
      }
    }
    :deep(.el-collapse-item__wrap) {
      border-bottom: none !important;
      background: none !important;
    }
    :deep(.el-collapse-item__content) {
      padding-bottom: 0 !important;
    }
  }
  .shared-button {
    padding: 10px 8px;
    font-weight: 400;
    font-size: 14px;
    margin-bottom: 4px;
    &.active {
      background: var(--el-color-primary-light-9);
      border-radius: var(--app-border-radius-small);
      color: var(--el-color-primary);
      font-weight: 500;
      &:hover {
        background: var(--el-color-primary-light-9);
      }
    }
    &:hover {
      border-radius: var(--app-border-radius-small);
      background: rgba(var(--el-text-color-primary-rgb), 0.1);
    }
    &.is-active {
      &:hover {
        color: var(--el-color-primary);
        background: var(--el-color-primary-light-9);
      }
    }
  }
}
</style>
