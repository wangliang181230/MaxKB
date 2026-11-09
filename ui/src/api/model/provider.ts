import {Result} from '@/request/Result'
import {get, post} from '@/request/index'
import type {Ref} from 'vue'
import type {Provider, BaseModel} from '@/api/type/model'
import type {FormField} from '@/components/dynamics-form/type'
import type {KeyValue} from '../type/common'
import useStore from '@/stores'

const prefix_provider = '/provider'
const get_workspace_prefix = () => {
  const {user} = useStore()
  return `/workspace/${user.getWorkspaceId()}${prefix_provider}`
}
/**
 * 获得供应商列表
 */
const getProvider: (loading?: Ref<boolean>) => Promise<Result<Array<Provider>>> = (loading) => {
  return get(`${prefix_provider}`, {}, loading)
}

/**
 * 获得各供应商下的模型数量
 */
const getProviderModelCount: (
  loading?: Ref<boolean>,
) => Promise<Result<Record<string, number>>> = (loading) => {
  return get(`${get_workspace_prefix()}/model_count`, {}, loading)
}

/**
 * 获得供应商列表
 */
const getProviderByModelType: (
  model_type: string,
  loading?: Ref<boolean>,
) => Promise<Result<Array<Provider>>> = (model_type, loading) => {
  return get(`${prefix_provider}`, {model_type}, loading)
}

/**
 * 获取模型创建表单
 * @param provider
 * @param model_type
 * @param model_name
 * @param loading
 * @returns
 */
const getModelCreateForm: (
  provider: string,
  model_type: string,
  model_name: string,
  loading?: Ref<boolean>,
) => Promise<Result<Array<FormField>>> = (provider, model_type, model_name, loading) => {
  return get(`${prefix_provider}/model_form`, {provider, model_type, model_name}, loading)
}

/**
 * 获取模型类型列表
 * @param provider 供应商
 * @param loading  加载器
 * @returns 模型类型列表
 */
const listModelType: (
  provider: string,
  loading?: Ref<boolean>,
) => Promise<Result<Array<KeyValue<string, string>>>> = (provider, loading?: Ref<boolean>) => {
  return get(`${prefix_provider}/model_type_list`, {provider}, loading)
}

/**
 * 获取基础模型列表
 * @param provider
 * @param model_type
 * @param loading
 * @returns
 */
const listBaseModel: (
  provider: string,
  model_type: string,
  loading?: Ref<boolean>,
) => Promise<Result<Array<BaseModel>>> = (provider, model_type, loading) => {
  return get(`${prefix_provider}/model_list`, {provider, model_type}, loading)
}

const listBaseModelParamsForm: (
  provider: string,
  model_type: string,
  model_name: string,
  loading?: Ref<boolean>,
) => Promise<Result<Array<BaseModel>>> = (provider, model_type, model_name, loading) => {
  return get(`${prefix_provider}/model_params_form`, {provider, model_type, model_name}, loading)
}
export default {
  getProvider,
  getProviderModelCount,
  getModelCreateForm,
  getProviderByModelType,
  listModelType,
  listBaseModel,
  listBaseModelParamsForm,
}
