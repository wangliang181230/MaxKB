# coding=utf-8
"""
    @project: MaxKB
    @Author：wangliang181230
    @file： api_key.py
    @date：2026/9/20 12:09
    @desc: 系统(个人) API Key 管理
"""
import hashlib

import uuid_utils.compat as uuid
from django.db.models import QuerySet
from django.utils import timezone
from rest_framework.request import Request
from rest_framework.views import APIView

from common.auth import TokenAuth
from common.auth.authentication import has_permissions
from common.constants.permission_constants import PermissionConstants, RoleConstants
from common.db.search import page_search
from common.exception.app_exception import AppApiException
from common.result import result
from system_manage.models import SystemApiKey

ORDER_BY_WHITE_LIST = ['create_time', '-create_time']


def _to_row(api_key: SystemApiKey):
    return {
        'id': api_key.id,
        'secret_key': api_key.secret_key,
        'is_active': api_key.is_active,
        'allow_cross_domain': api_key.allow_cross_domain,
        'cross_domain_list': api_key.cross_domain_list,
        'expire_time': api_key.expire_time,
        'is_permanent': api_key.is_permanent,
        'create_time': api_key.create_time,
        'update_time': api_key.update_time,
    }


class SystemApiKeyView(APIView):
    authentication_classes = [TokenAuth]

    @has_permissions(PermissionConstants.SYSTEM_API_KEY_EDIT, RoleConstants.ADMIN)
    def post(self, request: Request):
        secret_key = 'agent-' + hashlib.md5(str(uuid.uuid7()).encode()).hexdigest()
        api_key = SystemApiKey(id=uuid.uuid7(),
                               secret_key=secret_key,
                               user_id=str(request.user.id))
        api_key.save()
        return result.success(_to_row(api_key))

    class Page(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(PermissionConstants.SYSTEM_API_KEY_EDIT, RoleConstants.ADMIN)
        def get(self, request: Request, current_page, page_size):
            query_set = QuerySet(SystemApiKey).filter(user_id=str(request.user.id))
            order_by = request.query_params.get('order_by')
            query_set = query_set.order_by(order_by) if order_by in ORDER_BY_WHITE_LIST else query_set.order_by(
                '-create_time')
            return result.success(
                page_search(current_page, page_size, query_set, post_records_handler=_to_row))

    class Operate(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(PermissionConstants.SYSTEM_API_KEY_EDIT, RoleConstants.ADMIN)
        def delete(self, request: Request, api_key_id):
            QuerySet(SystemApiKey).filter(id=api_key_id, user_id=str(request.user.id)).delete()
            return result.success(True)

        @has_permissions(PermissionConstants.SYSTEM_API_KEY_EDIT, RoleConstants.ADMIN)
        def put(self, request: Request, api_key_id):
            api_key = QuerySet(SystemApiKey).filter(id=api_key_id, user_id=str(request.user.id)).first()
            if api_key is None:
                raise AppApiException(1004, 'APIKey does not exist')
            data = request.data
            if data.get('is_active') is not None:
                api_key.is_active = data.get('is_active')
            if data.get('allow_cross_domain') is not None:
                api_key.allow_cross_domain = data.get('allow_cross_domain')
            if data.get('cross_domain_list') is not None:
                api_key.cross_domain_list = data.get('cross_domain_list')
            if data.get('is_permanent') is not None:
                api_key.is_permanent = data.get('is_permanent')
                if not api_key.is_permanent:
                    expire_time = data.get('expire_time')
                    api_key.expire_time = expire_time if expire_time else timezone.now()
                else:
                    api_key.expire_time = timezone.now()
            api_key.save()
            return result.success(_to_row(api_key))
