# coding=utf-8
"""
    @project: MaxKB
    @Author：AI Assistant
    @file： long_term_memory.py
    @date：2025/7/9
    @desc: 长期记忆视图
"""
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework.request import Request
from rest_framework.views import APIView

from chat.api.chat_api import LongTermMemoryAPI
from chat.serializers.long_term_memory import LongTermMemoryQuerySerializer
from common.auth import ChatTokenAuth
from common.result import result


class LongTermMemoryView(APIView):
    authentication_classes = [ChatTokenAuth]

    @extend_schema(
        methods=['GET'],
        description=_('获取用户的长期记忆内容'),
        summary=_('获取用户的长期记忆内容'),
        operation_id=_('获取用户的长期记忆内容'),
        parameters=LongTermMemoryAPI.get_parameters(),
        responses=LongTermMemoryAPI.get_response(),
        tags=[_('Chat')]
    )
    def get(self, request: Request):
        """
        获取长期记忆
        参数通过 query 传递：
        - chat_user_id: 对话用户id（必填）
        - days: 查询最近几天的记忆，默认7天（可选）

        认证信息通过 Header 中的 Authorization: Bearer <api_key> 传递
        """
        serializer = LongTermMemoryQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        # 获取智能体ID（当前接口为我们公司自己用的接口，所以不从auth中取application_id，直接从application_ids参数中取）
        # application_id = request.auth.application_id
        application_ids = request.query_params.get('application_ids')  # ID字符串，用逗号隔开的
        if application_ids:
            application_ids = application_ids.split(',')
        else:
            application_ids = None

        result_data = serializer.query_long_term_memory({
            'chat_user_id': request.query_params.get('chat_user_id'),
            'application_ids': application_ids,
            'days': request.query_params.get('days')
        })

        return result.success(result_data)
