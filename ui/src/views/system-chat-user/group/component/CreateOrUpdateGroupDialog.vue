<template>
  <el-dialog :title="`${!isEdit ? $t('common.create') : $t('common.rename')}${$t('views.chatUser.group.title')}`"
    v-model="dialogVisible" :close-on-click-modal="false" :close-on-press-escape="false" :destroy-on-close="true">
    <el-form label-position="top" ref="formRef" :rules="rules" :model="form" require-asterisk-position="right" @submit.prevent>
      <el-form-item :label="`${$t('views.chatUser.group.title')}ID`" prop="id">
        <el-input v-model="form.id" maxlength="128" show-word-limit :disabled="isEdit"
          :placeholder="`${$t('common.inputPlaceholder')}${$t('views.chatUser.group.title')}ID`" />
      </el-form-item>
      <el-form-item :label="$t('views.chatUser.group.name')" prop="name">
        <el-input v-model="form.name" maxlength="128" show-word-limit
          :placeholder="`${$t('common.inputPlaceholder')}${$t('views.chatUser.group.name')}`" />
      </el-form-item>
    </el-form>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click.prevent="dialogVisible = false"> {{ $t('common.cancel') }} </el-button>
        <el-button type="primary" @click="submit(formRef)" :loading="loading">
          {{ !isEdit ? $t('common.create') : $t('common.save') }}
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import type { FormInstance } from 'element-plus'
import { MsgSuccess } from '@/utils/message'
import { t } from '@/locales'
import type { ListItem } from '@/api/type/common'
import {loadPermissionApi} from "@/utils/dynamics-api/permission-api.ts";


const emit = defineEmits<{
  (e: 'refresh', current: ListItem): void;
}>();

const dialogVisible = ref<boolean>(false)
const isEdit = ref<boolean>(false)
const defaultForm = {
  id: '',
  name: ''
}
const form = ref<ListItem>({
  ...defaultForm,
})
function open(item?: ListItem) {
  if (item) {
    isEdit.value = true
    form.value = { id: item.id, name: item.name }
  } else {
    isEdit.value = false
    form.value = { ...defaultForm }
  }
  dialogVisible.value = true
}

const formRef = ref<FormInstance>();

const rules = reactive({
  id: [{ required: true, message: `${t('common.inputPlaceholder')}ID`, trigger: 'blur' }],
  name: [{ required: true, message: `${t('common.inputPlaceholder')}${t('views.chatUser.group.name')}`, trigger: 'blur' }],
})

const loading = ref<boolean>(false)
const submit = async (formEl: FormInstance | undefined) => {
  if (!formEl) return
  await formEl.validate((valid) => {
    if (valid) {
      loadPermissionApi('userGroup').postUserGroup(form.value, loading).then((res: any) => {
        MsgSuccess(!isEdit.value ? t('common.createSuccess') : t('common.renameSuccess'))
        emit('refresh', res.data)
        dialogVisible.value = false
      })
    }
  })
}

defineExpose({ open })
</script>
