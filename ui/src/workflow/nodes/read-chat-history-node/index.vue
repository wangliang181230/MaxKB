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
          prop="chat_id"
          :rules="{
            message: $t('workflow.nodes.readChatHistoryNode.chatId.placeholder'),
            trigger: 'blur',
            required: true,
          }"
        >
          <template #label>
            <div class="flex-between">
              <div class="flex align-center">
                <span>{{ $t('aiChat.chatId') }}<span class="color-danger">*</span></span>
                <el-tooltip
                  effect="dark"
                  :content="$t('workflow.nodes.readChatHistoryNode.chatId.tooltip')"
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
            :placeholder="$t('workflow.nodes.readChatHistoryNode.chatId.placeholder')"
            v-model="form_data.chat_id"
          />
        </el-form-item>
      </el-form>
    </el-card>
  </NodeContainer>
</template>

<script setup lang="ts">
import { set } from 'lodash'
import NodeContainer from '@/workflow/common/NodeContainer.vue'
import NodeCascader from '@/workflow/common/NodeCascader.vue'
import { onMounted, ref, computed } from 'vue'

const props = defineProps<{ nodeModel: any }>()

const formRef = ref()
const nodeCascaderRef = ref()

const form_data = computed({
  get: () => {
    if (!props.nodeModel.properties.node_data) {
      set(props.nodeModel.properties, 'node_data', {
        chat_id: [],
      })
    } else {
      if (!props.nodeModel.properties.node_data.chat_id) {
        set(props.nodeModel.properties.node_data, 'chat_id', [])
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

onMounted(() => {
  set(props.nodeModel, 'validate', validate)
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

.ml-4 {
  margin-left: 4px;
}

.color-danger {
  color: var(--el-color-danger);
}
</style>
