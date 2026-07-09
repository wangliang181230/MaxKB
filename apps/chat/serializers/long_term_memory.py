# coding=utf-8
"""
    @project: MaxKB
    @Author：AI Assistant
    @file： long_term_memory.py
    @date：2025/7/9
    @desc: 长期记忆相关序列化器
"""
from datetime import timedelta, datetime

from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from application.models import ApplicationLongTermMemory, ApplicationApiKey, Application
from common.exception.app_exception import AppApiException
from common.utils.common import long_to_uuid


class LongTermMemoryQuerySerializer(serializers.Serializer):
    """
    长期记忆查询序列化器
    """
    chat_user_id = serializers.CharField(required=True, label=_('对话用户id'))
    application_ids = serializers.CharField(required=False, allow_null=True, allow_blank=True, label=_('智能体ID列表'))
    days = serializers.IntegerField(required=False, allow_null=True, min_value=1, label=_('查询天数'))

    class Meta:
        fields = ['chat_user_id', 'application_ids', 'days']

    def query_long_term_memory(self, instance: dict):
        """
        查询长期记忆
        :param instance: 包含 application_id, chat_user_id, days 的字典
        :return: 长期记忆内容
        """
        super().is_valid(raise_exception=True)

        chat_user_id = instance.get("chat_user_id")
        application_ids = instance.get('application_ids')
        days = instance.get("days")

        # chat_user_id 必填
        if not chat_user_id:
            raise AppApiException(500, _('请提供对话用户id'))

        # 如果 chat_user_id 是业务系统的 Long 型 ID（纯数字字符串），则转换为 UUID
        # 与 base_read_long_term_memory_node 保持一致的转换逻辑
        if isinstance(chat_user_id, str) and chat_user_id.isdigit():
            chat_user_id = str(long_to_uuid(int(chat_user_id)))

        # 查询长期记忆
        qs = QuerySet(ApplicationLongTermMemory).filter(chat_user_id=chat_user_id)
        if application_ids:
            qs = qs.filter(application_id__in=application_ids)
        # days 可能从 query_params 传入字符串，安全转换为 int，避免 str > int 比较报 TypeError
        try:
            days_int = int(days) if days else 0
        except (TypeError, ValueError):
            days_int = 0
        if days_int > 0:
            cutoff_date = datetime.now() - timedelta(days=days_int)
            qs = qs.filter(update_time__gte=cutoff_date)

        # 按更新时间倒序，优先返回最近的长期记忆；最多取200条。
        long_term_memory_list = list(qs.only('application_id', 'memory', 'create_time', 'update_time')
                                     .order_by('-update_time')[:200])

        return {
            'count': len(long_term_memory_list),
            'memories': [
                {
                    'application_id': str(item.application_id),
                    'memory': item.memory,
                    'create_time': item.create_time.strftime('%Y-%m-%d %H:%M:%S') if item.create_time else None,
                    'update_time': item.update_time.strftime('%Y-%m-%d %H:%M:%S') if item.update_time else None,
                }
                for item in long_term_memory_list
            ]
        }
