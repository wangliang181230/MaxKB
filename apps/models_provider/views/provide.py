# coding=utf-8

import hashlib

from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework.request import Request
from rest_framework.views import APIView

from common import result
from common.auth import TokenAuth
from common.auth.authentication import has_permissions
from common.constants.permission_constants import PermissionConstants, RoleConstants
from models_provider.api.provide import ProvideApi
from models_provider.constants.model_provider_constants import ModelProvideConstants
from models_provider.serializers.model_serializer import get_default_model_params_setting, \
    ProviderModelCountSerializer

# 模型供应商列表为静态目录数据，仅随版本升级 / model_type / 语言变化，与具体用户无关，
# 故通过 HTTP 缓存头（Cache-Control 强缓存 + ETag 协商缓存）让客户端在有效期内直接复用本地
# 缓存，过期后再凭 ETag 命中 304，避免重复传输。
PROVIDER_CACHE_MAX_AGE = 24 * 60 * 60  # 客户端强缓存时长（秒），可按需调整


def _etag_matches(if_none_match, etag):
    """判断请求头 If-None-Match 是否与当前 ETag 匹配（支持弱标记 W/ 与通配 *）。"""
    if not if_none_match:
        return False
    if if_none_match.strip() == '*':
        return True

    def normalize(value):
        value = value.strip()
        return value[2:] if value[:2].upper() == 'W/' else value

    return any(normalize(candidate) == etag for candidate in if_none_match.split(','))


class Provide(APIView):
    authentication_classes = [TokenAuth]

    @extend_schema(methods=['GET'],
                   summary=_('Get a list of model suppliers'),
                   description=_('Get a list of model suppliers'),
                   operation_id=_('Get a list of model suppliers'),  # type: ignore
                   responses=ProvideApi.get_response(),
                   tags=[_('Model')])  # type: ignore
    def get(self, request: Request):
        model_type = request.query_params.get('model_type')
        if model_type:
            providers = []
            for key in ModelProvideConstants.__members__:
                if len([item for item in ModelProvideConstants[key].value.get_model_type_list() if
                        item['value'] == model_type]) > 0:
                    providers.append(ModelProvideConstants[key].value.get_model_provide_info().to_dict())
        else:
            providers = [ModelProvideConstants[key].value.get_model_provide_info().to_dict() for key in
                         ModelProvideConstants.__members__]
        return self._with_cache_headers(request, result.success(providers))

    @staticmethod
    def _with_cache_headers(request: Request, response):
        """为静态供应商列表附加 HTTP 缓存头，命中协商缓存时返回 304。"""
        etag = '"%s"' % hashlib.md5(response.content).hexdigest()
        # 请求携带 Authorization 头，需 must-revalidate 浏览器才会缓存；名称随语言翻译，用 Vary 区分缓存。
        cache_control = 'private, max-age=%d, must-revalidate' % PROVIDER_CACHE_MAX_AGE
        if _etag_matches(request.headers.get('If-None-Match'), etag):
            response = HttpResponse(status=304)
        response['ETag'] = etag
        response['Cache-Control'] = cache_control
        response['Vary'] = 'Accept-Language'
        return response

    class ModelCount(APIView):
        authentication_classes = [TokenAuth]

        @extend_schema(methods=['GET'],
                       summary=_('Get the number of models for each supplier'),
                       description=_('Get the number of models for each supplier'),
                       operation_id=_('Get the number of models for each supplier'),  # type: ignore
                       responses=ProvideApi.ModelCount.get_response(),
                       tags=[_('Model')])  # type: ignore
        @has_permissions(PermissionConstants.MODEL_READ.get_workspace_permission(),
                         PermissionConstants.MODEL_READ.get_workspace_permission_workspace_manage_role(),
                         RoleConstants.WORKSPACE_MANAGE.get_workspace_role(), RoleConstants.USER.get_workspace_role())
        def get(self, request: Request, workspace_id: str):
            return result.success(
                ProviderModelCountSerializer(
                    data={'user_id': str(request.user.id), 'workspace_id': workspace_id}).get_model_count())

    class ModelTypeList(APIView):
        authentication_classes = [TokenAuth]

        @extend_schema(methods=['GET'],
                       summary=_('Get a list of model types'),
                       description=_('Get a list of model types'),
                       operation_id=_('Get a list of model types'),  # type: ignore
                       parameters=ProvideApi.ModelTypeList.get_query_params_api(),
                       responses=ProvideApi.ModelTypeList.get_response(),
                       tags=[_('Model')])  # type: ignore
        def get(self, request: Request):
            provider = request.query_params.get('provider')
            return result.success(ModelProvideConstants[provider].value.get_model_type_list())

    class ModelList(APIView):
        authentication_classes = [TokenAuth]

        @extend_schema(methods=['GET'],
                       summary=_('Example of obtaining model list'),
                       description=_('Example of obtaining model list'),
                       operation_id=_('Example of obtaining model list'),  # type: ignore
                       parameters=ProvideApi.ModelList.get_query_params_api(),
                       responses=ProvideApi.ModelList.get_response(),
                       tags=[_('Model')])  # type: ignore
        def get(self, request: Request):
            provider = request.query_params.get('provider')
            model_type = request.query_params.get('model_type')

            return result.success(
                ModelProvideConstants[provider].value.get_model_list(
                    model_type))

    class ModelParamsForm(APIView):
        authentication_classes = [TokenAuth]

        @extend_schema(methods=['GET'],
                       summary=_('Get model default parameters'),
                       description=_('Get model default parameters'),
                       operation_id=_('Get model default parameters'),  # type: ignore
                       parameters=ProvideApi.ModelParamsForm.get_query_params_api(),
                       responses=ProvideApi.ModelParamsForm.get_response(),
                       tags=[_('Model')])  # type: ignore
        def get(self, request: Request):
            provider = request.query_params.get('provider')
            model_type = request.query_params.get('model_type')
            model_name = request.query_params.get('model_name')

            return result.success(get_default_model_params_setting(provider, model_type, model_name))

    class ModelForm(APIView):
        authentication_classes = [TokenAuth]

        @extend_schema(methods=['GET'],
                       summary=_('Get the model creation form'),
                       description=_('Get the model creation form'),
                       operation_id=_('Get the model creation form'),  # type: ignore
                       parameters=ProvideApi.ModelParamsForm.get_query_params_api(),
                       responses=ProvideApi.ModelParamsForm.get_response(),
                       tags=[_('Model')])  # type: ignore
        def get(self, request: Request):
            provider = request.query_params.get('provider')
            model_type = request.query_params.get('model_type')
            model_name = request.query_params.get('model_name')
            return result.success(
                ModelProvideConstants[provider].value.get_model_credential(model_type, model_name).to_form_list())
