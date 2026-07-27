<template>
  <div>
    <div class="flex-between mb-8" v-if="content.tool_id && content.tool_record_id">
      <div></div>
      <el-button type="primary" link @click.stop="workflowDetailVisible = true">
        <el-icon class="mr-4"><Document /></el-icon>
        {{ $t('aiChat.executionDetails.workflowDetail') }}
      </el-button>
    </div>
    <p class="mt-8 mb-8">{{ $t('common.param.inputParam') }}：</p>
    <span class="color-secondary">{{ content.content.input }}</span>
    <p class="mt-8 mb-8">{{ $t('common.param.outputParam') }}：</p>
    <span class="color-secondary"><pre>{{ content.content.output }}</pre></span>
    <p class="mt-8 mb-8">
      {{ $t('aiChat.KnowledgeSource.consumeTime') }}：{{ content.run_time }} s
    </p>
    <el-dialog
      v-if="content.tool_id && content.tool_record_id"
      :title="$t('aiChat.executionDetails.workflowDetail')"
      v-model="workflowDetailVisible"
      destroy-on-close
      append-to-body
      align-center
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      width="800px"
    >
      <el-scrollbar height="60vh" v-loading="detailLoading">
        <template
          v-for="(item, index) in arraySort(
            Object.values(detailData?.meta?.details ?? {}),
            'index',
          )"
          :key="index"
        >
          <ExecutionDetailCard :data="item"></ExecutionDetailCard>
        </template>
        <el-empty v-if="!detailData || Object.keys(detailData?.meta?.details ?? {}).length === 0" />
      </el-scrollbar>
    </el-dialog>
  </div>
</template>
<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { type ToolCalls } from '@/components/markdown/tool-calls-render/index'
import { Document } from '@element-plus/icons-vue'
import ExecutionDetailCard from '@/components/execution-detail-card/index.vue'
import { arraySort } from '@/utils/array'
import toolApi from '@/api/tool/tool'
import chatAPI from '@/api/chat/chat'

const isChatPage = computed(() => {
  return window.MaxKB?.prefix.includes('/chat')
})

const props = defineProps<{
  content: ToolCalls
}>()

const workflowDetailVisible = ref(false)
const detailData = ref<any>(null)
const detailLoading = ref(false)

function getToolRecordDetail(tool_id: string, record_id: string) {
  if (isChatPage.value) {
    return chatAPI.getToolRecordDetail(tool_id, record_id)
  }
  return toolApi.getToolRecordDetail(tool_id, record_id)
}

watch(workflowDetailVisible, (val) => {
  if (val && props.content.tool_id && props.content.tool_record_id) {
    detailLoading.value = true
    getToolRecordDetail(props.content.tool_id, props.content.tool_record_id)
      .then((ok: any) => {
        detailData.value = ok.data
      })
      .finally(() => {
        detailLoading.value = false
      })
  }
})
</script>
<style lang="scss" scoped></style>
