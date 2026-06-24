# coding=utf-8
"""
    @project: MaxKB
    @Author: AI Assistant
    @file: i_a2a_node.py
    @date： 2026/06/24 16:20
    @desc: A2A (Agent-to-Agent) 节点接口定义 - 支持子代理委派和代理团队协作
"""
from typing import Type

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from application.flow.common import WorkflowMode
from application.flow.i_step_node import INode, NodeResult


class A2AAgentConfigSerializer(serializers.Serializer):
    """A2A代理配置序列化器"""
    agent_name = serializers.CharField(required=True, label=_('Agent Name'), max_length=100)
    agent_url = serializers.URLField(required=True, label=_('Agent URL'))
    protocol_type = serializers.ChoiceField(
        required=True,
        choices=[
            ('http', 'HTTP+SSE'),
            ('grpc', 'gRPC'),
        ],
        label=_('Protocol Type')
    )
    api_key = serializers.CharField(
        required=False, 
        label=_('API Key'), 
        allow_blank=True, 
        allow_null=True,
        help_text=_('Optional authentication key for the sub-agent')
    )
    timeout = serializers.IntegerField(
        required=False, 
        label=_('Timeout (seconds)'), 
        default=30,
        min_value=1,
        max_value=300
    )
    max_retries = serializers.IntegerField(
        required=False,
        label=_('Max Retries'),
        default=3,
        min_value=0,
        max_value=10
    )
    enable_streaming = serializers.BooleanField(
        required=False,
        label=_('Enable Streaming'),
        default=True,
        help_text=_('Support streaming pass-through for HTTP+SSE protocol')
    )


class A2ANodeParamsSerializer(serializers.Serializer):
    """A2A节点参数序列化器"""
    agent_config = A2AAgentConfigSerializer(required=True, label=_('Agent Configuration'))
    
    collaboration_mode = serializers.ChoiceField(
        required=True,
        choices=[
            ('subagent', _('Subagent (Delegation)')),
            ('team', _('Agent Team (Collaboration)')),
        ],
        label=_('Collaboration Mode'),
        help_text=_('Subagent: Single task delegation; Team: Multi-agent dynamic collaboration')
    )
    
    input_params = serializers.DictField(
        required=True,
        label=_('Input Parameters'),
        help_text=_('Parameters to pass to the sub-agent')
    )
    
    context_fields = serializers.ListField(
        required=False,
        label=_('Context Fields'),
        child=serializers.CharField(),
        default=[],
        help_text=_('Context fields to include in the request (e.g., history_context, user_id)')
    )
    
    output_mapping = serializers.DictField(
        required=False,
        label=_('Output Mapping'),
        default={},
        help_text=_('Map sub-agent response fields to workflow variables')
    )
    
    fallback_strategy = serializers.ChoiceField(
        required=False,
        choices=[
            ('error_message', _('Return Error Message')),
            ('skip', _('Skip and Continue')),
            ('default_value', _('Use Default Value')),
        ],
        label=_('Fallback Strategy'),
        default='error_message'
    )
    
    default_value = serializers.CharField(
        required=False,
        label=_('Default Value'),
        allow_blank=True,
        allow_null=True,
        help_text=_('Default value when fallback strategy is "Use Default Value"')
    )

    def is_valid(self, *, raise_exception=False):
        super().is_valid(raise_exception=raise_exception)
        
        # 验证协作模式特定要求
        collaboration_mode = self.validated_data.get('collaboration_mode')
        agent_config = self.validated_data.get('agent_config', {})
        
        if collaboration_mode == 'team':
            # Agent Team模式需要至少配置2个agent
            team_agents = self.initial_data.get('team_agents', [])
            if len(team_agents) < 2:
                raise serializers.ValidationError(
                    _('Agent Team mode requires at least 2 agents')
                )
        
        # 验证超时和重试配置
        timeout = agent_config.get('timeout', 30)
        max_retries = agent_config.get('max_retries', 3)
        
        if timeout * (max_retries + 1) > 600:
            raise serializers.ValidationError(
                _('Total timeout (timeout × retries) cannot exceed 600 seconds')
            )
        
        return True


class IA2ANode(INode):
    """A2A (Agent-to-Agent) 节点接口"""
    type = 'a2a-node'
    support = [
        WorkflowMode.APPLICATION, 
        WorkflowMode.APPLICATION_LOOP, 
        WorkflowMode.KNOWLEDGE,
        WorkflowMode.KNOWLEDGE_LOOP, 
        WorkflowMode.TOOL, 
        WorkflowMode.TOOL_LOOP
    ]

    def get_node_params_serializer_class(self) -> Type[serializers.Serializer]:
        return A2ANodeParamsSerializer

    def _run(self):
        return self.execute(**self.node_params_serializer.data, **self.flow_params_serializer.data)

    def execute(
        self, 
        agent_config, 
        collaboration_mode, 
        input_params,
        context_fields=None,
        output_mapping=None,
        fallback_strategy='error_message',
        default_value=None,
        **kwargs
    ) -> NodeResult:
        """
        执行A2A节点
        
        Args:
            agent_config: 代理配置信息
            collaboration_mode: 协作模式 (subagent/team)
            input_params: 输入参数
            context_fields: 上下文字段列表
            output_mapping: 输出映射
            fallback_strategy: 降级策略
            default_value: 默认值
            
        Returns:
            NodeResult: 节点执行结果
        """
        pass
