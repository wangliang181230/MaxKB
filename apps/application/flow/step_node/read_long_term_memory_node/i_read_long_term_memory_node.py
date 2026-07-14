# coding=utf-8
"""
    @project: MaxKB
    @Author：AI Assistant
    @file： i_read_long_term_memory_node.py
    @date：2026/07/14
    @desc: 读取长期记忆节点接口定义
"""
from typing import Type

from rest_framework import serializers

from application.flow.common import WorkflowMode
from application.flow.i_step_node import INode, NodeResult


class ReadLongTermMemoryNodeParamsSerializer(serializers.Serializer):
    """读取长期记忆节点参数序列化器"""

    chat_user_id = serializers.ListField(required=True, label="对话用户ID（引用路径）")
    chat_user_type = serializers.ListField(required=False, label="对话用户类型（引用路径）")
    application_ids = serializers.ListField(required=False,
                                            child=serializers.UUIDField(required=True),
                                            label="开启了长期记忆功能的高级智能体ID列表")
    days = serializers.IntegerField(required=False, default=0, label="查询天数")

    def is_valid(self, *, raise_exception=False):
        super().is_valid(raise_exception=True)
        return True


class IReadLongTermMemoryNode(INode):
    """读取长期记忆节点接口"""
    type = 'read-long-term-memory-node'
    support = [WorkflowMode.APPLICATION, WorkflowMode.APPLICATION_LOOP, WorkflowMode.TOOL, WorkflowMode.TOOL_LOOP]

    def get_node_params_serializer_class(self) -> Type[serializers.Serializer]:
        return ReadLongTermMemoryNodeParamsSerializer

    def _run(self):
        # 通过引用路径获取实际的 chat_user_id 值
        chat_user_id_ref = self.node_params_serializer.data.get('chat_user_id')
        print(f"\n{chat_user_id_ref}   ({type(chat_user_id_ref)})\n")
        if chat_user_id_ref and len(chat_user_id_ref) >= 2:
            chat_user_id = self.workflow_manage.get_reference_field(
                chat_user_id_ref[0],
                chat_user_id_ref[1:]
            )
        else:
            chat_user_id = ''

        # 通过引用路径获取实际的 chat_user_type 值
        chat_user_type_ref = self.node_params_serializer.data.get('chat_user_type')
        print(f"\n{chat_user_type_ref}   ({type(chat_user_type_ref)})\n")
        if chat_user_type_ref and len(chat_user_type_ref) >= 2:
            chat_user_type = self.workflow_manage.get_reference_field(
                chat_user_type_ref[0],
                chat_user_type_ref[1:]
            )
        else:
            chat_user_type = ''

        application_ids = self.node_params_serializer.data.get('application_ids', [])
        days = int(self.node_params_serializer.data.get('days') or 0)

        return self.execute(
            chat_user_id=chat_user_id,
            chat_user_type=chat_user_type,
            application_ids=application_ids,
            days=days,
        )

    def execute(self, chat_user_id, chat_user_type, application_ids, days=0, **kwargs) -> NodeResult:
        """执行读取长期记忆"""
        pass