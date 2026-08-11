<template>
  <NodeContainer :nodeModel="nodeModel">
    <el-form
      :model="form_data"
      label-position="top"
      require-asterisk-position="right"
      label-width="auto"
      ref="SwitchNodeFormRef"
      @submit.prevent
    >
      <!-- 变量选择 -->
      <el-form-item
        :label="$t('workflow.nodes.switchNode.variable')"
        prop="field"
        :rules="{
          type: 'array',
          required: true,
          message: $t('workflow.variable.placeholder'),
          trigger: 'change',
        }"
      >
        <NodeCascader
          ref="nodeCascaderRef"
          :nodeModel="nodeModel"
          class="w-full"
          :placeholder="$t('workflow.variable.placeholder')"
          v-model="form_data.field"
        />
      </el-form-item>

      <!-- Case 分支列表 -->
      <VueDraggable
        ref="el"
        v-bind:modelValue="form_data.branch"
        :disabled="form_data.branch.length === 2"
        handle=".handle"
        :animation="150"
        ghostClass="ghost"
        @end="onEnd"
      >
        <template v-for="(item, index) in form_data.branch" :key="item.id">
          <el-card
            v-resize="(wh: any) => resizeBranch(wh, item, index)"
            shadow="never"
            class="drag-card card-never mb-8"
            :class="{
              'no-drag': item.type === 'DEFAULT' || form_data.branch.length === 2,
            }"
            style="--el-card-padding: 12px"
          >
            <div class="flex-between lighter">
              <span class="flex align-center">
                <img
                  v-if="item.type !== 'DEFAULT'"
                  src="@/assets/sort.svg"
                  alt=""
                  height="15"
                  class="handle handle-img mr-4"
                />
                <span :class="item.type === 'DEFAULT' ? 'ml-20' : ''">{{ item.type }}</span>
              </span>
              <el-button
                v-if="item.type !== 'DEFAULT'"
                link
                type="info"
                @click="deleteBranch(index)"
              >
                <AppIcon iconName="app-delete"></AppIcon>
              </el-button>
            </div>
            <div v-if="item.type !== 'DEFAULT'" class="mt-8">
              <el-form-item
                :prop="'branch.' + index + '.value'"
                :rules="{
                  required: true,
                  message: $t('workflow.nodes.switchNode.valueMessage'),
                  trigger: 'blur',
                }"
              >
                <el-input
                  v-model="item.value"
                  :placeholder="$t('workflow.nodes.switchNode.valuePlaceholder')"
                />
              </el-form-item>
            </div>
          </el-card>
        </template>
      </VueDraggable>

      <el-button link type="primary" @click="addCase">
        <AppIcon iconName="app-add-outlined" class="mr-4"></AppIcon>
        {{ $t('workflow.nodes.switchNode.addCase') }}
      </el-button>
    </el-form>
  </NodeContainer>
</template>
<script setup lang="ts">
import { cloneDeep, set } from 'lodash'
import NodeContainer from '@/workflow/common/NodeContainer.vue'
import NodeCascader from '@/workflow/common/NodeCascader.vue'
import type { FormInstance } from 'element-plus'
import { ref, computed, onMounted } from 'vue'
import { randomId } from '@/utils/common'
import { VueDraggable } from 'vue-draggable-plus'

const props = defineProps<{ nodeModel: any }>()

const form = {
  field: [],
  branch: [
    {
      id: randomId(),
      type: 'CASE 1',
      value: '',
    },
    {
      id: randomId(),
      type: 'DEFAULT',
      value: '',
    },
  ],
}

const resizeBranch = (wh: any, row: any, index: number) => {
  const branch_condition_list = cloneDeep(
    props.nodeModel.properties.branch_condition_list
      ? props.nodeModel.properties.branch_condition_list
      : [],
  )
  const new_branch_condition_list = branch_condition_list.map((item: any) => {
    if (item.id === row.id) {
      return { ...item, height: wh.height, index: index }
    }
    return item
  })
  set(props.nodeModel.properties, 'branch_condition_list', new_branch_condition_list)
  refreshBranchAnchor(props.nodeModel.properties.node_data.branch, true)
}

const form_data = computed({
  get: () => {
    if (props.nodeModel.properties.node_data) {
      return props.nodeModel.properties.node_data
    } else {
      set(props.nodeModel.properties, 'node_data', form)
      refreshBranchAnchor(form.branch, true)
    }
    return props.nodeModel.properties.node_data
  },
  set: (value) => {
    set(props.nodeModel.properties, 'node_data', value)
  },
})

const SwitchNodeFormRef = ref<FormInstance>()
const nodeCascaderRef = ref()

const validate = () => {
  const v_list = [
    SwitchNodeFormRef.value?.validate(),
    ...(nodeCascaderRef.value ? [nodeCascaderRef.value.validate()] : []),
  ]
  return Promise.all(v_list).catch((err) => {
    return Promise.reject({ node: props.nodeModel, errMessage: err })
  })
}

function onEnd(event?: any) {
  const { oldIndex, newIndex } = event
  if (oldIndex === undefined || newIndex === undefined) return
  const list = cloneDeep(props.nodeModel.properties.node_data.branch)
  // Prevent moving DEFAULT
  const lastIdx = list.length - 1
  if (oldIndex === lastIdx || newIndex === lastIdx) return
  const newInstance = { ...list[oldIndex], type: list[newIndex].type, id: list[newIndex].id }
  const oldInstance = { ...list[newIndex], type: list[oldIndex].type, id: list[oldIndex].id }
  list[newIndex] = newInstance
  list[oldIndex] = oldInstance
  set(props.nodeModel.properties.node_data, 'branch', list)
}

function addCase() {
  const list = cloneDeep(props.nodeModel.properties.node_data.branch)
  const caseCount = list.filter((item: any) => item.type !== 'DEFAULT').length
  const obj = {
    id: randomId(),
    type: 'CASE ' + (caseCount + 1),
    value: '',
  }
  list.splice(list.length - 1, 0, obj)
  refreshBranchAnchor(list, true)
  set(props.nodeModel.properties.node_data, 'branch', list)
}

function deleteBranch(index: number) {
  const list = cloneDeep(props.nodeModel.properties.node_data.branch)
  const deleted = list.splice(index, 1)
  const delete_target_anchor_id_list = deleted.map(
    (item: any) => props.nodeModel.id + '_' + item.id + '_right',
  )
  props.nodeModel.graphModel.eventCenter.emit(
    'delete_edge',
    props.nodeModel.outgoing.edges
      .filter((item: any) => delete_target_anchor_id_list.includes(item.sourceAnchorId))
      .map((item: any) => item.id),
  )
  refreshBranchAnchor(list, false)
  set(props.nodeModel.properties.node_data, 'branch', list)
}

function refreshBranchAnchor(list: Array<any>, is_add: boolean) {
  const branch_condition_list = cloneDeep(
    props.nodeModel.properties.branch_condition_list
      ? props.nodeModel.properties.branch_condition_list
      : [],
  )
  const new_branch_condition_list = list
    .map((item, index) => {
      const find = branch_condition_list.find((b: any) => b.id === item.id)
      if (find) {
        return { index: index, height: find.height, id: item.id }
      } else {
        if (is_add) {
          return { index: index, height: 12, id: item.id }
        }
      }
    })
    .filter((item) => item)

  set(props.nodeModel.properties, 'branch_condition_list', new_branch_condition_list)
  props.nodeModel.refreshBranch()
}

onMounted(() => {
  set(props.nodeModel, 'validate', validate)
})
</script>
<style lang="scss" scoped>
.ml-20 {
  margin-left: 20px;
}
</style>
