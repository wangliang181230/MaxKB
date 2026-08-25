<template>
  <el-drawer
    v-model="debugVisible"
    size="60%"
    :append-to-body="true"
    :modal="false"
    :show-close="false"
  >
    <template #header>
      <div class="flex align-center" style="margin-left: -8px">
        <el-button class="cursor mr-4" link @click.prevent="debugVisible = false">
          <el-icon :size="20">
            <Back />
          </el-icon>
        </el-button>
        <h4>{{ $t('common.debug') }}</h4>
      </div>
    </template>
    <div>
      <div v-if="form.init_field_list.length > 0" class="mb-16">
        <h4 class="title-decoration-1 mb-16">
          {{ $t('common.param.initParam') }}
        </h4>
        <el-card shadow="never" class="card-never" style="--el-card-padding: 12px">
          <DynamicsForm
            v-model="form.init_params"
            :model="form.init_params"
            label-position="top"
            require-asterisk-position="right"
            :render_data="form.init_field_list"
            ref="dynamicsFormRef"
          >
          </DynamicsForm>
        </el-card>
      </div>
      <div v-if="form.debug_field_list.length > 0" class="mb-16">
        <h4 class="title-decoration-1 mb-16">
          {{ $t('common.param.inputParam') }}
        </h4>
        <el-card shadow="never" class="card-never" style="--el-card-padding: 12px">
          <el-form
            ref="FormRef"
            :model="form"
            label-position="top"
            require-asterisk-position="right"
            hide-required-asterisk
            v-loading="loading"
            @submit.prevent
          >
            <template v-for="(item, index) in form.debug_field_list" :key="index">
              <el-form-item
                :label="item.name"
                :prop="'debug_field_list.' + index + '.value'"
                :rules="{
                  required: item.is_required,
                  message: $t('views.tool.form.param.inputPlaceholder'),
                  trigger: 'blur',
                }"
              >
                <template #label>
                  <div class="flex">
                    <span
                      >{{ item.name }}
                      <el-tooltip
                        v-if="item.desc"
                        effect="dark"
                        placement="right"
                        popper-class="max-w-200"
                      >
                        <template #content>
                          {{ item.desc }}
                        </template>
                        <AppIcon iconName="app-warning" class="app-warning-icon"></AppIcon>
                      </el-tooltip>
                      <span class="color-danger" v-if="item.is_required">*</span></span
                    >
                    <el-tag size="small" type="info" class="info-tag ml-4">{{ item.type }}</el-tag>
                  </div>
                </template>
                <el-input
                  v-model="item.value"
                  :placeholder="$t('views.tool.form.param.inputPlaceholder')"
                />
              </el-form-item>
            </template>
          </el-form>
        </el-card>
      </div>

      <el-button type="primary" @click="submit(FormRef)" :loading="loading">
        {{ $t('views.tool.form.debug.run') }}
      </el-button>
      <div v-if="showResult" class="mt-8">
        <h4 class="title-decoration-1 mb-16 mt-16">
          {{ $t('views.tool.form.debug.runResult') }}
        </h4>
        <div class="mb-16">
          <el-alert
            v-if="isSuccess"
            :title="$t('views.tool.form.debug.runSuccess')"
            type="success"
            show-icon
            :closable="false"
          />
          <el-alert
            v-else
            :title="$t('views.tool.form.debug.runFailed')"
            type="error"
            show-icon
            :closable="false"
          />
        </div>

        <p class="lighter mb-8">{{ $t('views.tool.form.debug.output') }}</p>

        <el-card :class="isSuccess ? '' : 'color-danger'" class="pre-wrap" shadow="never">
          {{ String(result) == '0' ? 0 : result || '-' }}
        </el-card>
      </div>
    </div>
  </el-drawer>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed, nextTick } from 'vue'
import type { FormInstance } from 'element-plus'
import { useRoute } from 'vue-router'
import DynamicsForm from '@/components/dynamics-form/index.vue'
import { loadSharedApi } from '@/utils/dynamics-api/shared-api'

const route = useRoute()

const apiType = computed(() => {
  if (route.path.includes('shared')) {
    return 'systemShare'
  } else if (route.path.includes('resource-management')) {
    return 'systemManage'
  } else {
    return 'workspace'
  }
})
const FormRef = ref()
const dynamicsFormRef = ref()
const loading = ref(false)
const debugVisible = ref(false)
const showResult = ref(false)
const isSuccess = ref(false)
const result = ref('')

const form = ref<any>({
  debug_field_list: [],
  code: '',
  input_field_list: [],
  init_field_list: [],
  init_params: {},
})

watch(debugVisible, (bool) => {
  if (!bool) {
    showResult.value = false
    isSuccess.value = false
    result.value = ''
    form.value = {
      debug_field_list: [],
      code: '',
      input_field_list: [],
      init_field_list: [],
      init_params: {},
    }
  }
})

const submit = async (formEl: FormInstance | undefined) => {
  const validate = formEl ? formEl.validate() : Promise.resolve()
  Promise.all([dynamicsFormRef.value?.validate(), validate]).then(() => {
    loadSharedApi({ type: 'tool', systemType: apiType.value })
      .postToolDebug(form.value, loading)
      .then((res: any) => {
        if (res.code === 500) {
          showResult.value = true
          isSuccess.value = false
          result.value = res.message
        } else {
          showResult.value = true
          isSuccess.value = true
          result.value = res.data
        }
      })
  })
}

const open = (data: any) => {
  if (data.input_field_list.length > 0) {
    data.input_field_list.forEach((item: any) => {
      form.value.debug_field_list.push({
        value: (item.default_value || ''),
        ...item,
      })
    })
  }
  form.value.code = data.code
  form.value.input_field_list = data.input_field_list
  form.value.init_field_list = (data.init_field_list || []).map((item: any) => {
    if (item.input_type === 'PasswordInput') {
      return {
        ...item,
        default_value: undefined, // 清除密码框的默认值
        attrs: { ...(item.attrs || {}), autocomplete: 'new-password' }, // 添加 autocomplete 属性到 PasswordInput，屏蔽浏览器的密码自动填充功能
      }
    }
    return item
  })
  const password_fields = (data.init_field_list || [])
    .filter((item: any) => item.input_type === 'PasswordInput')
    .map((item: any) => item.field)
  const init_params = (data.init_field_list || [])
    .map((item: any) => {
      if (password_fields.includes(item.field)) {
        return { [item.field]: undefined }
      }
      if (item.show_default_value === false) {
        return { [item.field]: undefined }
      }
      return { [item.field]: item.default_value }
    })
    .reduce((x: any, y: any) => ({ ...x, ...y }), {})
  const data_init_params = { ...(data.init_params || {}) }
  password_fields.forEach((field: string) => {
    delete data_init_params[field]
  })
  form.value.init_params = { ...init_params, ...data_init_params }
  debugVisible.value = true
  nextTick(() => {
    setTimeout(() => {
      const containers: Array<{ el: HTMLElement; requiredOnly: boolean }> = []
      if (dynamicsFormRef.value?.$el) {
        containers.push({ el: dynamicsFormRef.value.$el as HTMLElement, requiredOnly: true })
      }
      if (FormRef.value?.$el) {
        containers.push({ el: FormRef.value.$el as HTMLElement, requiredOnly: true })
      }
      if (dynamicsFormRef.value?.$el) {
        containers.push({ el: dynamicsFormRef.value.$el as HTMLElement, requiredOnly: false })
      }
      if (FormRef.value?.$el) {
        containers.push({ el: FormRef.value.$el as HTMLElement, requiredOnly: false })
      }
      for (const { el, requiredOnly } of containers) {
        const items = el.querySelectorAll(':scope > .el-form-item')
        if (requiredOnly) {
          const requiredItem = el.querySelector('.is-required')
          if (requiredItem === null) {
            continue
          }
          const input = requiredItem.querySelector('input') as HTMLInputElement | null
          if (input && !input.value) {
            input.focus()
            return
          }
        } else {
          for (const item of items) {
            const input = item.querySelector('input') as HTMLInputElement | null
            if (input && !input.value) {
              input.focus()
              return
            }
          }
        }
      }
    }, 300)
  })
}

defineExpose({
  open,
})
</script>
<style lang="scss"></style>
