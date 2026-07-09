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


class LongTermMemoryQuerySerializer(serializers.Serializer):
    """
    长期记忆查询序列化器
    """
    chat_user_id = serializers.CharField(required=True, label=_('对话用户id'))
    application_ids = serializers.CharField(required=False, allow_null=True, allow_blank=True, label=_('智能体ID列表'))
    days = serializers.IntegerField(required=False, allow_null=True, min_value=1, label=_('查询天数'))

    class Meta:
        fields = ['chat_user_id', 'application_ids', 'days']

    def is_valid(self, raise_exception=False):
        super().is_valid(raise_exception=True)
        return True

    def query_long_term_memory(self, instance: dict):
        """
        查询长期记忆
        :param instance: 包含 application_id, chat_user_id, days 的字典
        :return: 长期记忆内容
        """
        self.is_valid(raise_exception=True)

        chat_user_id = instance.get("chat_user_id")
        application_ids = instance.get('application_ids')
        days = instance.get("days")

        # chat_user_id 必填
        if not chat_user_id:
            raise AppApiException(500, _('请提供对话用户id'))

        # 查询长期记忆
        qs = QuerySet(ApplicationLongTermMemory).filter(chat_user_id=chat_user_id)
        if application_ids:
            qs = qs.filter(application_id__in=application_ids)
        if days and days > 0:
            # 计算时间范围
            cutoff_date = datetime.now() - timedelta(days=float(days))
            qs = qs.filter(update_time__gte=cutoff_date)
        long_term_memory_list = qs.order_by('-update_time')

        if long_term_memory_list.exists():
            return {
                'count': long_term_memory_list.count(),
                'memories': [
                    {
                        'application_id': str(item.application_id),
                        'memory': item.memory,
                        'create_time': item.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'update_time': item.update_time.strftime('%Y-%m-%d %H:%M:%S'),
                    }
                    for item in long_term_memory_list
                ]
            }
        else:
            return {
                'count': 0,
                'memories': [],
            }
