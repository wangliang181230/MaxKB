# coding=utf-8
"""
    @project: MaxKB
    @Author：虎虎
    @file： log_management.py
    @date：2025/6/4 14:15
    @desc: 操作日志
"""
import datetime
import json
from io import BytesIO

from django.db.models import QuerySet
from django.http import StreamingHttpResponse
from django.utils.translation import gettext_lazy as _
from rest_framework.request import Request
from rest_framework.views import APIView

from common.auth import TokenAuth
from common.auth.authentication import has_permissions
from common.constants.permission_constants import PermissionConstants, RoleConstants
from common.db.search import page_search
from common.result import result
from system_manage.models import Log, SystemSetting as SystemSettingModel, SettingType

DEFAULT_CLEAN_TIME = 180


def _build_query_set(query):
    """
    根据查询条件构造日志查询集
    @param query: 查询参数(query_params 或 request.data)
    @return: QuerySet
    """
    query_set = QuerySet(Log)
    start_time = query.get('start_time')
    end_time = query.get('end_time')
    if start_time:
        query_set = query_set.filter(create_time__date__gte=start_time)
    if end_time:
        query_set = query_set.filter(create_time__date__lte=end_time)
    user = query.get('user')
    if user:
        query_set = query_set.filter(user__username__icontains=user)
    status = query.get('status')
    if status:
        query_set = query_set.filter(status=status)
    ip_address = query.get('ip_address')
    if ip_address:
        query_set = query_set.filter(ip_address__icontains=ip_address)
    menu = query.get('menu')
    if menu:
        try:
            menu_list = json.loads(menu)
            if isinstance(menu_list, list) and len(menu_list) > 0:
                query_set = query_set.filter(menu__in=menu_list)
        except Exception:
            pass
    workspace_ids = query.get('workspace_ids')
    if workspace_ids:
        try:
            workspace_id_list = json.loads(workspace_ids)
            if isinstance(workspace_id_list, list) and len(workspace_id_list) > 0:
                query_set = query_set.filter(workspace_id__in=workspace_id_list)
        except Exception:
            pass
    return query_set.order_by('-create_time')


def _to_row(log_model: Log):
    return {
        'id': log_model.id,
        'menu': log_model.menu,
        'operate': log_model.operate,
        'operation_object': log_model.operation_object,
        'user': log_model.user,
        'status': log_model.status,
        'ip_address': log_model.ip_address,
        'details': log_model.details,
        'workspace_id': log_model.workspace_id,
        'create_time': log_model.create_time,
    }


class OperateLog(APIView):
    class Page(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(PermissionConstants.OPERATION_LOG_READ, RoleConstants.ADMIN)
        def get(self, request: Request, current_page, page_size):
            query_set = _build_query_set(request.query_params)
            return result.success(
                page_search(current_page, page_size, query_set, post_records_handler=_to_row))

    class MenuOperationOption(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(PermissionConstants.OPERATION_LOG_READ, RoleConstants.ADMIN)
        def get(self, request: Request):
            menu_list = [item.get('menu') for item in QuerySet(Log).values('menu').distinct() if item.get('menu')]
            return result.success([{'menu': menu, 'menu_label': menu} for menu in menu_list])

    class Export(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(PermissionConstants.OPERATION_LOG_EXPORT, RoleConstants.ADMIN)
        def post(self, request: Request):
            import openpyxl
            query_set = _build_query_set(request.data)

            def stream_response():
                workbook = openpyxl.Workbook(write_only=True)
                worksheet = workbook.create_sheet(title='Sheet1')
                headers = [str(_('Operation menu')), str(_('Operation')), str(_('Operation object')),
                           str(_('user')), str(_('Status')), str(_('Ip Address')), str(_('Operate Time'))]
                worksheet.append(headers)
                for log_model in query_set:
                    operation_object = log_model.operation_object or {}
                    user = log_model.user or {}
                    worksheet.append([
                        log_model.menu,
                        log_model.operate,
                        operation_object.get('name', '') if isinstance(operation_object, dict) else '',
                        user.get('username', '') if isinstance(user, dict) else '',
                        str(_('Success')) if log_model.status == 200 else str(_('Fail')),
                        log_model.ip_address,
                        log_model.create_time.strftime('%Y-%m-%d %H:%M:%S') if log_model.create_time else '',
                    ])
                output = BytesIO()
                workbook.save(output)
                output.seek(0)
                yield output.getvalue()
                output.close()
                workbook.close()

            response = StreamingHttpResponse(
                stream_response(),
                content_type='application/vnd.open.xmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename="log.xlsx"'
            return response

    class SaveCleanTime(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(PermissionConstants.OPERATION_LOG_CLEAR_POLICY, RoleConstants.ADMIN)
        def post(self, request: Request):
            clean_time = request.data.get('clean_time', DEFAULT_CLEAN_TIME)
            try:
                clean_time = int(clean_time)
            except (TypeError, ValueError):
                clean_time = DEFAULT_CLEAN_TIME
            SystemSettingModel.objects.update_or_create(
                type=SettingType.LOG.value,
                defaults={'meta': {'clean_time': clean_time}})
            # 清理 clean_time 天前的日志
            deadline = datetime.datetime.now() - datetime.timedelta(days=clean_time)
            QuerySet(Log).filter(create_time__lt=deadline).delete()
            return result.success(True)

    class GetCleanTime(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(PermissionConstants.OPERATION_LOG_READ, RoleConstants.ADMIN)
        def get(self, request: Request):
            system_setting = QuerySet(SystemSettingModel).filter(type=SettingType.LOG.value).first()
            clean_time = DEFAULT_CLEAN_TIME
            if system_setting is not None and isinstance(system_setting.meta, dict):
                clean_time = system_setting.meta.get('clean_time', DEFAULT_CLEAN_TIME)
            return result.success(clean_time)
