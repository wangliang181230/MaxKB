# coding=utf-8
"""
    @project: MaxKB
    @Author：wangliang181230
    @file： chat_user.py
    @date：2026/9/20 12:09
    @desc: 对话用户 / 用户组管理
"""
import json

import uuid_utils.compat as uuid
from django.db import transaction
from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _
from rest_framework.request import Request
from rest_framework.views import APIView

from common.auth import TokenAuth
from common.auth.authentication import has_permissions
from common.constants.permission_constants import PermissionConstants, RoleConstants
from common.db.search import page_search
from common.exception.app_exception import AppApiException
from common.log.log import log
from common.result import result
from common.utils.common import password_encrypt
from common.utils.rsa_util import decrypt
from system_manage.models import ChatUser, UserGroup, UserGroupRelation

ORDER_BY_WHITE_LIST = ['create_time', '-create_time', 'username', '-username', 'nick_name', '-nick_name']


def _set_user_groups(user_id, group_ids):
    """
    重置对话用户所属用户组
    """
    QuerySet(UserGroupRelation).filter(user_id=user_id).delete()
    for group_id in group_ids or []:
        if QuerySet(UserGroup).filter(id=group_id).exists():
            UserGroupRelation(id=uuid.uuid7(), user_id=user_id, group_id=group_id).save()


def _to_chat_user_row(chat_user: ChatUser):
    relations = QuerySet(UserGroupRelation).filter(user_id=chat_user.id)
    group_ids = [relation.group_id for relation in relations]
    group_names = [group.name for group in QuerySet(UserGroup).filter(id__in=group_ids)]
    return {
        'id': chat_user.id,
        'username': chat_user.username,
        'nick_name': chat_user.nick_name,
        'email': chat_user.email,
        'phone': chat_user.phone,
        'source': chat_user.source,
        'is_active': chat_user.is_active,
        'create_time': chat_user.create_time,
        'update_time': chat_user.update_time,
        'user_group_ids': group_ids,
        'user_group_names': group_names,
    }


def _to_group_user_row(relation: UserGroupRelation):
    chat_user = relation.user
    return {
        'id': chat_user.id,
        'email': chat_user.email,
        'phone': chat_user.phone,
        'nick_name': chat_user.nick_name,
        'username': chat_user.username,
        'source': chat_user.source,
        'is_active': chat_user.is_active,
        'create_time': chat_user.create_time,
        'update_time': chat_user.update_time,
        'user_group_relation_id': relation.id,
    }


class ChatUserView(APIView):
    authentication_classes = [TokenAuth]

    @has_permissions(PermissionConstants.CHAT_USER_READ, RoleConstants.ADMIN)
    def get(self, request: Request):
        chat_user_list = QuerySet(ChatUser).order_by('-create_time')[:200]
        return result.success([
            {'id': chat_user.id, 'username': chat_user.username, 'nick_name': chat_user.nick_name}
            for chat_user in chat_user_list])

    @log(menu='Chat User', operate='Create chat user',
         get_operation_object=lambda r, k: {'name': r.data.get('username', None)})
    @has_permissions(PermissionConstants.CHAT_USER_CREATE, RoleConstants.ADMIN)
    @transaction.atomic
    def post(self, request: Request):
        data = request.data
        password = data.get('password')
        if data.get('encrypted'):
            password = decrypt(password)
        username = data.get('username')
        nick_name = data.get('nick_name')
        email = data.get('email') or None
        if QuerySet(ChatUser).filter(username=username).exists():
            raise AppApiException(1004, _('Username is already in use'))
        if nick_name and QuerySet(ChatUser).filter(nick_name=nick_name).exists():
            raise AppApiException(1004, _('Nickname is already in use'))
        if email and QuerySet(ChatUser).filter(email=email).exists():
            raise AppApiException(1004, _('Email is already in use'))
        chat_user = ChatUser(
            id=uuid.uuid7(),
            username=username,
            nick_name=nick_name,
            email=email,
            phone=data.get('phone', ''),
            password=password_encrypt(password),
            source=data.get('source', 'LOCAL'),
            is_active=True)
        chat_user.save()
        _set_user_groups(chat_user.id, data.get('user_group_ids', []))
        return result.success(_to_chat_user_row(chat_user))

    class Page(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(PermissionConstants.CHAT_USER_READ, RoleConstants.ADMIN)
        def get(self, request: Request, current_page, page_size):
            query = request.query_params
            query_set = QuerySet(ChatUser)
            username = query.get('username')
            nick_name = query.get('nick_name')
            source = query.get('source')
            is_active = query.get('is_active')
            if username:
                query_set = query_set.filter(username__icontains=username)
            if nick_name:
                query_set = query_set.filter(nick_name__icontains=nick_name)
            if source:
                query_set = query_set.filter(source=source)
            if is_active is not None and is_active != '':
                query_set = query_set.filter(is_active=is_active in [True, 'true', 'True'])
            order_by = query.get('order_by')
            query_set = query_set.order_by(order_by) if order_by in ORDER_BY_WHITE_LIST else query_set.order_by(
                '-create_time')
            return result.success(
                page_search(current_page, page_size, query_set, post_records_handler=_to_chat_user_row))

    class Operate(APIView):
        authentication_classes = [TokenAuth]

        @log(menu='Chat User', operate='Delete chat user')
        @has_permissions(PermissionConstants.CHAT_USER_DELETE, RoleConstants.ADMIN)
        def delete(self, request: Request, user_id):
            QuerySet(ChatUser).filter(id=user_id).delete()
            return result.success(True)

        @log(menu='Chat User', operate='Update chat user')
        @has_permissions(PermissionConstants.CHAT_USER_EDIT, RoleConstants.ADMIN)
        @transaction.atomic
        def put(self, request: Request, user_id):
            chat_user = QuerySet(ChatUser).filter(id=user_id).first()
            if chat_user is None:
                raise AppApiException(1004, _('User does not exist'))
            data = request.data
            nick_name = data.get('nick_name')
            if nick_name and QuerySet(ChatUser).filter(nick_name=nick_name).exclude(id=user_id).exists():
                raise AppApiException(1004, _('Nickname is already in use'))
            email = data.get('email')
            if email and QuerySet(ChatUser).filter(email=email).exclude(id=user_id).exists():
                raise AppApiException(1004, _('Email is already in use'))
            if nick_name:
                chat_user.nick_name = nick_name
            if 'email' in data:
                chat_user.email = email or None
            if 'phone' in data:
                chat_user.phone = data.get('phone', '')
            if data.get('is_active') is not None:
                chat_user.is_active = data.get('is_active')
            chat_user.save()
            if 'user_group_ids' in data:
                _set_user_groups(chat_user.id, data.get('user_group_ids', []))
            return result.success(_to_chat_user_row(chat_user))

    class RePassword(APIView):
        authentication_classes = [TokenAuth]

        @log(menu='Chat User', operate='Change chat user password')
        @has_permissions(PermissionConstants.CHAT_USER_EDIT, RoleConstants.ADMIN)
        def put(self, request: Request, user_id):
            data = dict(request.data)
            encrypted_data = data.get('encryptedData', '')
            if encrypted_data:
                decrypted_raw = decrypt(encrypted_data)
                decrypted = json.loads(decrypted_raw) if decrypted_raw else {}
                if isinstance(decrypted, dict):
                    data = {**data, **decrypted}
            password = data.get('password')
            re_password = data.get('re_password')
            if not password or password != re_password:
                raise AppApiException(500, _('Passwords do not match'))
            chat_user = QuerySet(ChatUser).filter(id=user_id).first()
            if chat_user is None:
                raise AppApiException(1004, _('User does not exist'))
            chat_user.password = password_encrypt(password)
            chat_user.save()
            return result.success(True)

    class BatchAddGroup(APIView):
        authentication_classes = [TokenAuth]

        @log(menu='Chat User', operate='Set chat user groups')
        @has_permissions(PermissionConstants.CHAT_USER_GROUP, RoleConstants.ADMIN)
        @transaction.atomic
        def post(self, request: Request):
            data = request.data
            ids = data.get('ids', [])
            user_group_ids = data.get('user_group_ids', [])
            is_append = data.get('is_append', True)
            for user_id in ids:
                if is_append:
                    existing = {str(relation.group_id) for relation in
                                QuerySet(UserGroupRelation).filter(user_id=user_id)}
                    for group_id in user_group_ids:
                        if str(group_id) not in existing and QuerySet(UserGroup).filter(id=group_id).exists():
                            UserGroupRelation(id=uuid.uuid7(), user_id=user_id, group_id=group_id).save()
                else:
                    _set_user_groups(user_id, user_group_ids)
            return result.success(True)

    class BatchDelete(APIView):
        authentication_classes = [TokenAuth]

        @log(menu='Chat User', operate='Batch delete chat user')
        @has_permissions(PermissionConstants.CHAT_USER_DELETE, RoleConstants.ADMIN)
        def post(self, request: Request):
            ids = request.data
            QuerySet(ChatUser).filter(id__in=ids).delete()
            return result.success(True)

    class SyncTypes(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(PermissionConstants.CHAT_USER_SYNC, RoleConstants.ADMIN)
        def get(self, request: Request):
            return result.success([])

    class Sync(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(PermissionConstants.CHAT_USER_SYNC, RoleConstants.ADMIN)
        def post(self, request: Request, sync_type):
            return result.success({'success_count': 0, 'conflict_users': []})


class UserGroupView(APIView):
    authentication_classes = [TokenAuth]

    @has_permissions(PermissionConstants.USER_GROUP_READ, RoleConstants.ADMIN)
    def get(self, request: Request):
        group_list = QuerySet(UserGroup).all()
        return result.success([{'id': group.id, 'name': group.name} for group in group_list])

    @log(menu='User Group', operate='Create or update user group',
         get_operation_object=lambda r, k: {'name': r.data.get('name', None)})
    @has_permissions(PermissionConstants.USER_GROUP_CREATE, PermissionConstants.USER_GROUP_EDIT, RoleConstants.ADMIN)
    def post(self, request: Request):
        data = request.data
        group_id = data.get('id')
        name = data.get('name')
        # 用户组ID必须由前端填写（业务系统通过角色代码关联），不由后端生成
        if not group_id:
            raise AppApiException(1004, _('User group id is required'))
        if not name:
            raise AppApiException(1004, _('User group name is required'))
        group = QuerySet(UserGroup).filter(id=group_id).first()
        if group is not None:
            # 已存在则重命名
            if QuerySet(UserGroup).filter(name=name).exclude(id=group_id).exists():
                raise AppApiException(1004, _('User group name is already in use'))
            group.name = name
            group.save()
            return result.success({'id': group.id, 'name': group.name})
        # 不存在则使用前端传入的ID创建
        if QuerySet(UserGroup).filter(name=name).exists():
            raise AppApiException(1004, _('User group name is already in use'))
        group = UserGroup(id=str(group_id), name=name)
        group.save()
        return result.success({'id': group.id, 'name': group.name})

    class Operate(APIView):
        authentication_classes = [TokenAuth]

        @log(menu='User Group', operate='Delete user group')
        @has_permissions(PermissionConstants.USER_GROUP_DELETE, RoleConstants.ADMIN)
        def delete(self, request: Request, user_group_id):
            QuerySet(UserGroup).filter(id=user_group_id).delete()
            return result.success(True)

    class AddMember(APIView):
        authentication_classes = [TokenAuth]

        @log(menu='User Group', operate='Add member to user group')
        @has_permissions(PermissionConstants.USER_GROUP_ADD_MEMBER, RoleConstants.ADMIN)
        @transaction.atomic
        def post(self, request: Request, user_group_id):
            user_ids = request.data.get('user_ids', [])
            existing = {str(relation.user_id) for relation in
                        QuerySet(UserGroupRelation).filter(group_id=user_group_id)}
            for user_id in user_ids:
                if str(user_id) not in existing:
                    UserGroupRelation(id=uuid.uuid7(), user_id=user_id, group_id=user_group_id).save()
            return result.success(True)

    class RemoveMember(APIView):
        authentication_classes = [TokenAuth]

        @log(menu='User Group', operate='Remove member from user group')
        @has_permissions(PermissionConstants.USER_GROUP_REMOVE_MEMBER, RoleConstants.ADMIN)
        def post(self, request: Request, user_group_id):
            relation_ids = request.data.get('group_relation_ids', [])
            QuerySet(UserGroupRelation).filter(id__in=relation_ids, group_id=user_group_id).delete()
            return result.success(True)

    class UserList(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(PermissionConstants.USER_GROUP_READ, RoleConstants.ADMIN)
        def get(self, request: Request, user_group_id, current_page, page_size):
            query = request.query_params
            relation_query_set = QuerySet(UserGroupRelation).filter(group_id=user_group_id)
            username = query.get('username')
            nick_name = query.get('nick_name')
            source = query.get('source')
            if username:
                relation_query_set = relation_query_set.filter(user__username__icontains=username)
            if nick_name:
                relation_query_set = relation_query_set.filter(user__nick_name__icontains=nick_name)
            if source:
                relation_query_set = relation_query_set.filter(user__source=source)
            relation_query_set = relation_query_set.order_by('id')
            return result.success(
                page_search(current_page, page_size, relation_query_set, post_records_handler=_to_group_user_row))
