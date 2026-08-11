# coding=utf-8
"""
    @project: maxkb
    @Author：虎
    @file： i_switch_node.py
    @date：2024/6/7 9:54
    @desc:
"""
from typing import Type

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from application.flow.common import WorkflowMode
from application.flow.i_step_node import INode


class SwitchCaseSerializer(serializers.Serializer):
    id = serializers.CharField(required=True, label=_("Branch id"))
    type = serializers.CharField(required=True, label=_("Branch Type"))
    value = serializers.CharField(required=False, allow_blank=True, allow_null=True, label=_("Case value"))


class SwitchNodeParamsSerializer(serializers.Serializer):
    field = serializers.ListField(required=True, label=_("Variable field"))
    branch = SwitchCaseSerializer(many=True)


class ISwitchNode(INode):
    def get_node_params_serializer_class(self) -> Type[serializers.Serializer]:
        return SwitchNodeParamsSerializer

    type = 'switch-node'

    support = [WorkflowMode.APPLICATION, WorkflowMode.APPLICATION_LOOP, WorkflowMode.KNOWLEDGE,
               WorkflowMode.KNOWLEDGE_LOOP, WorkflowMode.TOOL, WorkflowMode.TOOL_LOOP]
