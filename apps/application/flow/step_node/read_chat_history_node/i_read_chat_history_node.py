# coding=utf-8
"""
    @project: MaxKB
    @Author：AI Assistant
    @file： i_read_chat_history_node.py
    @date：2026/08/06
    @desc: 读取历史对话节点接口定义
"""
from typing import Type

from rest_framework import serializers

from application.flow.common import WorkflowMode
from application.flow.i_step_node import INode, NodeResult


class ReadChatHistoryNodeParamsSerializer(serializers.Serializer):
    """读取历史对话节点参数序列化器"""

    chat_id = serializers.ListField(required=True, label="对话ID（引用路径）")

    def is_valid(self, *, raise_exception=False):
        super().is_valid(raise_exception=True)
        return True


class IReadChatHistoryNode(INode):
    """读取历史对话节点接口"""
    type = 'read-chat-history-node'
    support = [WorkflowMode.APPLICATION, WorkflowMode.APPLICATION_LOOP, WorkflowMode.TOOL, WorkflowMode.TOOL_LOOP]

    def get_node_params_serializer_class(self) -> Type[serializers.Serializer]:
        return ReadChatHistoryNodeParamsSerializer

    def _run(self):
        # 通过引用路径获取实际的 chat_id 值
        chat_id_ref = self.node_params_serializer.data.get('chat_id')
        if chat_id_ref and len(chat_id_ref) >= 2:
            chat_id = self.workflow_manage.get_reference_field(
                chat_id_ref[0],
                chat_id_ref[1:]
            )
        else:
            chat_id = ''

        return self.execute(
            chat_id=chat_id,
        )

    def execute(self, chat_id, **kwargs) -> NodeResult:
        """执行读取历史对话"""
        pass
