<template>
  <NodeContainer :nodeModel="nodeModel">
    <h5 class="title-decoration-1 mb-8">{{ $t('workflow.nodeSetting') }}</h5>
    <el-card shadow="never" class="card-never">
      <el-form
        @submit.prevent
        :model="form_data"
        label-position="top"
        require-asterisk-position="right"
        label-width="auto"
        ref="formRef"
        hide-required-asterisk
      >
        <el-form-item
          prop="chat_user_id"
          :rules="{
            message: $t('workflow.nodes.readLongTermMemoryNode.chatUserId.placeholder'),
            trigger: 'blur',
            required: true,
          }"
        >
          <template #label>
            <div class="flex-between">
              <div class="flex align-center">
                <span>{{ $t('aiChat.chatUserId') }}<span class="color-danger">*</span></span>
                <el-tooltip
                  effect="dark"
                  :content="$t('workflow.nodes.readLongTermMemoryNode.chatUserId.tooltip')"
                  placement="right"
                >
                  <AppIcon iconName="app-warning" class="app-warning-icon ml-4"></AppIcon>
                </el-tooltip>
              </div>
            </div>
          </template>
          <NodeCascader
            ref="nodeCascaderRef"
            :nodeModel="nodeModel"
            class="w-full"
            :placeholder="$t('workflow.nodes.readLongTermMemoryNode.chatUserId.placeholder')"
            v-model="form_data.chat_user_id"
          />
        </el-form-item>

        <el-form-item prop="chat_user_type">
          <template #label>
            <div class="flex-between">
              <div class="flex align-center">
                <span>{{ $t('aiChat.chatUserType') }}</span>
                <el-tooltip
                  effect="dark"
                  :content="$t('workflow.nodes.readLongTermMemoryNode.chatUserType.tooltip')"
                  placement="right"
                >
                  <AppIcon iconName="app-warning" class="app-warning-icon ml-4"></AppIcon>
                </el-tooltip>
              </div>
            </div>
          </template>
          <NodeCascader
            ref="nodeCascaderRef"
            :nodeModel="nodeModel"
            class="w-full"
            :placeholder="$t('workflow.nodes.readLongTermMemoryNode.chatUserType.placeholder')"
            v-model="form_data.chat_user_type"
          />
        </el-form-item>

        <el-form-item prop="application_ids">
          <template #label>
            <div class="flex-between">
              <span>{{ $t('workflow.nodes.readLongTermMemoryNode.applicationList.label') }}</span>
              <el-dropdown trigger="click" @command="handleApplicationSelect">
                <el-button type="primary" link>
                  <AppIcon iconName="app-add-outlined"></AppIcon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu class="application-dropdown-menu">
                    <el-dropdown-item
                      v-for="app in applicationList"
                      :key="app.id"
                      :command="app"
                      :disabled="form_data.application_ids?.includes(app.id)"
                    >
                      <div class="flex align-center">
                        <AppIcon iconName="app-agent" class="mr-8" :size="16" />
                        <span :title="getApplicationTitle(app.id, app.name)">{{ app.name }}</span>
                        <el-icon v-if="form_data.application_ids?.includes(app.id)" class="ml-auto">
                          <Check />
                        </el-icon>
                      </div>
                    </el-dropdown-item>
                    <el-dropdown-item v-if="applicationList.length === 0" disabled>
                      <el-text type="info">{{ $t('common.noData') }}</el-text>
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </template>
          <div class="w-full">
            <el-text type="info" v-if="!form_data.application_ids || form_data.application_ids?.length === 0">
              {{ $t('workflow.nodes.readLongTermMemoryNode.applicationList.placeholder') }}
            </el-text>
            <template v-for="(item, index) in form_data.application_ids" :key="index" v-else>
              <div class="flex-between border border-r-6 white-bg mb-4" style="padding: 5px 8px">
                <div class="flex align-center" style="line-height: 20px" :title="getApplicationTitle(item)">
                  <AppIcon iconName="app-agent" class="mr-8" :size="20" />
                  <div class="ellipsis">
                    {{ getApplicationName(item) }}
                  </div>
                </div>
                <el-button text @click="removeApplication(item)">
                  <el-icon>
                    <Close />
                  </el-icon>
                </el-button>
              </div>
            </template>
          </div>
        </el-form-item>

        <el-form-item prop="days">
          <template #label>
            <div class="flex-between">
              <div class="flex align-center">
                <span>{{ $t('workflow.nodes.readLongTermMemoryNode.days.label') }}</span>
                <el-tooltip
                  effect="dark"
                  :content="$t('workflow.nodes.readLongTermMemoryNode.days.tooltip')"
                  placement="right"
                >
                  <AppIcon iconName="app-warning" class="app-warning-icon ml-4"></AppIcon>
                </el-tooltip>
              </div>
            </div>
          </template>
          <el-input-number
            v-model="form_data.days"
            :min="0"
            :max="365"
            :step="1"
            :placeholder="$t('workflow.nodes.readLongTermMemoryNode.days.placeholder')"
            controls-position="right"
            class="w-full"
            @change="(val: number) => set(props.nodeModel.properties.node_data, 'days', val)"
          />
        </el-form-item>
      </el-form>
    </el-card>
  </NodeContainer>
</template>

<script setup lang="ts">
import { set, get } from 'lodash'
import NodeContainer from '@/workflow/common/NodeContainer.vue'
import NodeCascader from '@/workflow/common/NodeCascader.vue'
import { onMounted, ref, computed } from 'vue'
import { Close, Check } from '@element-plus/icons-vue'
import { loadSharedApi } from '@/utils/dynamics-api/shared-api'
import useStore from '@/stores'

const props = defineProps<{ nodeModel: any }>()
const { user } = useStore()

const formRef = ref()
const nodeCascaderRef = ref()
const applicationList = ref<any[]>([])

const form_data = computed({
  get: () => {
    if (!props.nodeModel.properties.node_data) {
      set(props.nodeModel.properties, 'node_data', {
        chat_user_id: [],
        chat_user_type: [],
        application_ids: [],
        days: 0
      })
    } else {
      if (!props.nodeModel.properties.node_data.chat_user_id) {
        set(props.nodeModel.properties.node_data, 'chat_user_id', [])
      }
      if (!props.nodeModel.properties.node_data.chat_user_type) {
        set(props.nodeModel.properties.node_data, 'chat_user_type', [])
      }
      if (!props.nodeModel.properties.node_data.application_ids) {
        set(props.nodeModel.properties.node_data, 'application_ids', [])
      }
      if (props.nodeModel.properties.node_data.days === undefined || props.nodeModel.properties.node_data.days === null) {
        set(props.nodeModel.properties.node_data, 'days', 0)
      }
    }
    return props.nodeModel.properties.node_data
  },
  set: (value) => {
    set(props.nodeModel.properties, 'node_data', value)
  },
})

const validate = () => {
  return formRef.value?.validate()
}

const loadApplicationList = async () => {
  try {
    const res = await loadSharedApi({
      type: 'application',
      systemType: 'workspace',
    }).getAllApplication({
      folder_id: user.getWorkspaceId(),
    })
    applicationList.value = (res.data || []).filter(
      (app: any) => app.resource_type === 'application' && app.is_publish && app.long_term_enable
    )
  } catch (error) {
    console.error('加载应用列表失败:', error)
  }
}

const handleApplicationSelect = (app: any) => {
  const current_ids = form_data.value.application_ids || []
  if (!current_ids.includes(app.id)) {
    set(props.nodeModel.properties.node_data, 'application_ids', [...current_ids, app.id])
  }
}

const removeApplication = (appId: string) => {
  const list = (form_data.value.application_ids || []).filter((id: string) => id !== appId)
  set(props.nodeModel.properties.node_data, 'application_ids', list)
}

const getApplicationName = (appId: string) => {
  const app = applicationList.value.find(a => a.id === appId)
  return app?.name || appId
}

const getApplicationTitle = (appId: string, appName?: string) => {
  if (appName) {
    return `${appName}  ${appId}`
  } else {
    const app = applicationList.value.find(a => a.id === appId)
    return app?.name ? `${app?.name}  ${appId}` : appId
  }
}

onMounted(() => {
  set(props.nodeModel, 'validate', validate)
  // 加载应用列表
  loadApplicationList()
})
</script>

<style lang="scss" scoped>
.title-decoration-1 {
  font-size: 14px;
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.mb-8 {
  margin-bottom: 8px;
}

.w-full {
  width: 100%;
}

.flex-between {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.flex {
  display: flex;
}

.align-center {
  align-items: center;
}

.mr-8 {
  margin-right: 8px;
}

.ellipsis {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.border {
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
}

.white-bg {
  background-color: var(--el-bg-color);
}

.mb-4 {
  margin-bottom: 4px;
}

.color-danger {
  color: var(--el-color-danger);
}

.color-secondary {
  color: var(--el-text-color-secondary);
}

.lighter {
  font-weight: lighter;
}

.ml-auto {
  margin-left: auto;
}
</style>

<style lang="scss">
.application-dropdown-menu {
  max-height: 300px;
  overflow-y: auto;

  .el-dropdown-menu__item {
    padding: 8px 12px;

    &:hover:not(.is-disabled) {
      background-color: var(--el-fill-color-light);
    }

    &.is-disabled {
      cursor: not-allowed;
    }
  }
}
</style>
