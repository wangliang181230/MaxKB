<template>
  <NodeContainer :nodeModel="nodeModel">
    <h5 class="title-decoration-1 mb-8">{{ $t('workflow.nodeSetting') }}</h5>

    <!-- 基本配置 -->
    <div class="border-r-6 p-8-12 mb-8 layout-bg lighter">
      <el-form
        @submit.prevent
        :model="form_data"
        label-position="top"
        require-asterisk-position="right"
        label-width="auto"
        ref="a2aNodeFormRef"
        hide-required-asterisk
      >
        <el-form-item :label="$t('workflow.nodes.a2aNode.agentName')" required>
          <el-input
            v-model="form_data.agent_config.agent_name"
            :placeholder="$t('workflow.nodes.a2aNode.agentNamePlaceholder')"
          />
        </el-form-item>

        <el-form-item :label="$t('workflow.nodes.a2aNode.agentUrl')" required>
          <el-input
            v-model="form_data.agent_config.agent_url"
            :placeholder="$t('workflow.nodes.a2aNode.agentUrlPlaceholder')"
          />
        </el-form-item>

        <el-form-item :label="$t('workflow.nodes.a2aNode.protocolType')" required>
          <el-select
            v-model="form_data.agent_config.protocol_type"
            :teleported="false"
            style="width: 100%"
          >
            <el-option
              label="HTTP+SSE"
              value="http"
            >
              <span>HTTP+SSE</span>
              <el-tag size="small" type="success" class="ml-8">
                {{ $t('workflow.nodes.a2aNode.streaming') }}
              </el-tag>
            </el-option>
            <el-option
              label="gRPC"
              value="grpc"
            >
              <span>gRPC</span>
              <el-tag size="small" type="info" class="ml-8">
                {{ $t('workflow.nodes.a2aNode.comingSoon') }}
              </el-tag>
            </el-option>
          </el-select>
        </el-form-item>

        <el-form-item :label="$t('workflow.nodes.a2aNode.collaborationMode')" required>
          <el-radio-group v-model="form_data.collaboration_mode">
            <el-radio label="subagent">
              {{ $t('workflow.nodes.a2aNode.subagentMode') }}
              <el-tooltip :content="$t('workflow.nodes.a2aNode.subagentTooltip')" placement="top">
                <AppIcon iconName="app-info" class="ml-4" style="cursor: help" />
              </el-tooltip>
            </el-radio>
            <el-radio label="team">
              {{ $t('workflow.nodes.a2aNode.teamMode') }}
              <el-tooltip :content="$t('workflow.nodes.a2aNode.teamTooltip')" placement="top">
                <AppIcon iconName="app-info" class="ml-4" style="cursor: help" />
              </el-tooltip>
            </el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item :label="$t('workflow.nodes.a2aNode.apiKey')">
          <el-input
            v-model="form_data.agent_config.api_key"
            type="password"
            show-password
            :placeholder="$t('workflow.nodes.a2aNode.apiKeyPlaceholder')"
          />
        </el-form-item>
      </el-form>
    </div>

    <!-- 高级配置 -->
    <h5 class="title-decoration-1 mb-8">
      {{ $t('workflow.nodes.a2aNode.advancedConfig') }}
    </h5>
    <div class="border-r-6 p-8-12 mb-8 layout-bg lighter">
      <el-form
        @submit.prevent
        :model="form_data"
        label-position="top"
      >
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item :label="$t('workflow.nodes.a2aNode.timeout')">
              <el-input-number
                v-model="form_data.agent_config.timeout"
                :min="1"
                :max="300"
                style="width: 100%"
              />
              <div class="form-tip">{{ $t('workflow.nodes.a2aNode.timeoutTip') }}</div>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item :label="$t('workflow.nodes.a2aNode.maxRetries')">
              <el-input-number
                v-model="form_data.agent_config.max_retries"
                :min="0"
                :max="10"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item :label="$t('workflow.nodes.a2aNode.enableStreaming')">
          <el-switch v-model="form_data.agent_config.enable_streaming" />
          <div class="form-tip ml-8">{{ $t('workflow.nodes.a2aNode.streamingTip') }}</div>
        </el-form-item>
      </el-form>
    </div>

    <!-- 输入参数配置 -->
    <h5 class="title-decoration-1 mb-8">
      {{ $t('workflow.nodes.a2aNode.inputParams') }}
    </h5>
    <div class="border-r-6 p-8-12 mb-8 layout-bg lighter">
      <el-alert
        :title="$t('workflow.nodes.a2aNode.inputParamsTip')"
        type="info"
        :closable="false"
        show-icon
      />
      <div class="mt-8">
        <el-button type="primary" link @click="addInputParam">
          <AppIcon iconName="app-add-outlined" class="mr-4"></AppIcon>
          {{ $t('workflow.nodes.a2aNode.addParam') }}
        </el-button>
      </div>
      <div v-if="Object.keys(form_data.input_params).length > 0 || editingParamKey !== null" class="mt-8">
        <div
          v-for="(value, key) in form_data.input_params"
          :key="key"
          class="flex-between mb-8 p-8 border-r-6 layout-bg"
        >
          <div class="flex align-center flex-1">
            <span class="mr-8 font-medium">{{ key }}</span>
            <el-tag size="small">{{ typeof value === 'string' ? 'string' : typeof value }}</el-tag>
          </div>
          <el-button link type="danger" @click="removeInputParam(key)">
            <AppIcon iconName="app-delete"></AppIcon>
          </el-button>
        </div>

        <!-- 正在编辑的新参数 -->
        <div v-if="editingParamKey !== null" class="mb-8 p-8 border-r-6 primary-light">
          <div class="flex align-center">
            <el-input
              ref="editingInputRef"
              v-model="editingParamKey"
              :placeholder="$t('workflow.nodes.a2aNode.paramKeyPlaceholder')"
              size="small"
              @keyup.enter="confirmNewParam"
              @keyup.esc="cancelNewParam"
              class="flex-1"
            >
              <template #prefix>
                <AppIcon iconName="app-edit" style="cursor: pointer" />
              </template>
              <template #suffix>
                <div class="flex align-center">
                  <el-button
                    link
                    type="info"
                    size="small"
                    @click.stop="cancelNewParam"
                  >
                    <AppIcon iconName="app-delete"></AppIcon>
                  </el-button>
                </div>
              </template>
            </el-input>
          </div>
          <div class="form-tip mt-4">
            {{ $t('workflow.nodes.a2aNode.paramEditTip') }}
          </div>
        </div>
      </div>
      <div v-else class="color-secondary text-center mt-8">
        {{ $t('common.noData') }}
      </div>
    </div>

    <!-- 上下文配置 -->
    <h5 class="title-decoration-1 mb-8">
      {{ $t('workflow.nodes.a2aNode.contextFields') }}
    </h5>
    <div class="border-r-6 p-8-12 mb-8 layout-bg lighter">
      <el-form-item>
        <el-select
          v-model="form_data.context_fields"
          multiple
          filterable
          :teleported="false"
          style="width: 100%"
          :placeholder="$t('workflow.nodes.a2aNode.selectContextFields')"
        >
          <el-option
            v-for="field in availableContextFields"
            :key="field.value"
            :label="field.label"
            :value="field.value"
          />
        </el-select>
        <div class="form-tip">{{ $t('workflow.nodes.a2aNode.contextFieldsTip') }}</div>
      </el-form-item>
    </div>

    <!-- 降级策略 -->
    <h5 class="title-decoration-1 mb-8">
      {{ $t('workflow.nodes.a2aNode.fallbackStrategy') }}
    </h5>
    <div class="border-r-6 p-8-12 mb-8 layout-bg lighter">
      <el-form
        @submit.prevent
        :model="form_data"
        label-position="top"
      >
        <el-form-item :label="$t('workflow.nodes.a2aNode.fallbackStrategyLabel')">
          <el-select
            v-model="form_data.fallback_strategy"
            :teleported="false"
            style="width: 100%"
          >
            <el-option
              :label="$t('workflow.nodes.a2aNode.fallbackErrorMessage')"
              value="error_message"
            />
            <el-option
              :label="$t('workflow.nodes.a2aNode.fallbackSkip')"
              value="skip"
            />
            <el-option
              :label="$t('workflow.nodes.a2aNode.fallbackDefaultValue')"
              value="default_value"
            />
          </el-select>
        </el-form-item>

        <el-form-item
          v-if="form_data.fallback_strategy === 'default_value'"
          :label="$t('workflow.nodes.a2aNode.defaultValueLabel')"
        >
          <el-input
            v-model="form_data.default_value"
            type="textarea"
            :rows="3"
            :placeholder="$t('workflow.nodes.a2aNode.defaultValuePlaceholder')"
          />
        </el-form-item>
      </el-form>
    </div>
  </NodeContainer>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import NodeContainer from '@/workflow/common/NodeContainer.vue'
import { AppNodeModel } from '@/workflow/common/app-node'
import { t } from '@/locales'
import AppIcon from '@/components/app-icon/AppIcon.vue'

const props = defineProps<{
  nodeModel: AppNodeModel
}>()

const form_data = ref({
  agent_config: {
    agent_name: '',
    agent_url: '',
    protocol_type: 'http',
    api_key: '',
    timeout: 30,
    max_retries: 3,
    enable_streaming: true,
  },
  collaboration_mode: 'subagent',
  input_params: {} as Record<string, any>,
  context_fields: [] as string[],
  output_mapping: {} as Record<string, string>,
  fallback_strategy: 'error_message',
  default_value: null as any,
})

const editingParamKey = ref<string | null>(null)
const editingInputRef = ref<HTMLInputElement>()

const availableContextFields = computed(() => [
  { label: t('workflow.nodes.startNode.question'), value: 'question' },
  { label: t('workflow.nodes.startNode.currentTime'), value: 'time' },
  { label: t('views.application.form.historyRecord.label'), value: 'history_context' },
  { label: t('aiChat.chatId'), value: 'aiChat_id' },
])

const addInputParam = async () => {
  // 如果已经在编辑中，不允许重复添加
  if (editingParamKey.value !== null) {
    return
  }

  // 设置编辑状态为空字符串，触发输入框显示
  editingParamKey.value = ''

  // 等待DOM更新后自动聚焦
  await nextTick()
  editingInputRef.value?.focus()
}

const confirmNewParam = () => {
  const key = editingParamKey.value?.trim()

  if (!key) {
    cancelNewParam()
    return
  }

  // 检查是否已存在
  if (form_data.value.input_params[key]) {
    ElMessage.warning(t('workflow.nodes.a2aNode.paramExists'))
    return
  }

  // 添加新参数，默认值为空字符串
  form_data.value.input_params[key] = ''

  // 清空编辑状态
  editingParamKey.value = null
}

const cancelNewParam = () => {
  editingParamKey.value = null
}

const removeInputParam = (key: string) => {
  delete form_data.value.input_params[key]
}

onMounted(() => {
  // 加载已有配置
  const nodeData = props.nodeModel.properties.node_data || {}
  if (Object.keys(nodeData).length > 0) {
    form_data.value = { ...form_data.value, ...nodeData }
  }
})

// 监听表单变化，自动保存
watch(
  form_data,
  (newVal) => {
    props.nodeModel.setProperties({
      ...props.nodeModel.properties,
      node_data: newVal,
    })
  },
  { deep: true }
)
</script>

<style scoped lang="scss">
.form-tip {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
}

.primary-light {
  background-color: var(--el-color-primary-light-9);
  border-left: 3px solid var(--el-color-primary);
}

.font-medium {
  font-weight: 500;
}
</style>
