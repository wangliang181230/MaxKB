# coding=utf-8
"""
    @project: MaxKB
    @Author：AI Assistant
    @file： base_a2a_node.py
    @date：2026/06/22
    @desc: A2A (Agent-to-Agent) 节点实现 - 支持HTTP+SSE和gRPC协议
"""
import json
import time
import uuid
import asyncio
from typing import Dict, Any, Optional, List

import aiohttp
import requests
from django.utils.translation import gettext_lazy as _

from application.flow.i_step_node import NodeResult
from application.flow.step_node.a2a_node.i_a2a_node import IA2ANode
from common.exception.app_exception import AppApiException


class BaseA2ANode(IA2ANode):
    """A2A (Agent-to-Agent) 节点实现类"""
    
    def save_context(self, details, workflow_manage):
        """保存上下文"""
        self.context['result'] = details.get('result')
        self.context['response_time'] = details.get('response_time')
        self.context['protocol_type'] = details.get('protocol_type')
        self.context['collaboration_mode'] = details.get('collaboration_mode')
        self.context['agent_name'] = details.get('agent_name')
        self.context['status_code'] = details.get('status_code')
        self.context['exception_message'] = details.get('err_message')
        self.context['retry_count'] = details.get('retry_count', 0)

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
        执行A2A节点调用
        """
        if context_fields is None:
            context_fields = []
        if output_mapping is None:
            output_mapping = {}
            
        start_time = time.time()
        retry_count = 0
        max_retries = agent_config.get('max_retries', 3)
        timeout = agent_config.get('timeout', 30)
        protocol_type = agent_config.get('protocol_type', 'http')
        agent_url = agent_config.get('agent_url')
        agent_name = agent_config.get('agent_name')
        api_key = agent_config.get('api_key')
        enable_streaming = agent_config.get('enable_streaming', True)
        
        # 生成TraceID用于全链路追踪
        trace_id = str(uuid.uuid4())
        
        # 构建请求头
        headers = {
            'Content-Type': 'application/json',
            'X-Request-Id': trace_id,
            'X-Agent-Name': agent_name,
            'X-Collaboration-Mode': collaboration_mode,
        }
        
        # 如果有API Key，添加到请求头
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'
        
        # 构建请求体
        request_body = self._build_request_body(
            input_params, 
            context_fields, 
            trace_id,
            collaboration_mode
        )
        
        last_error = None
        result = None
        
        # 重试机制
        while retry_count <= max_retries:
            try:
                if protocol_type == 'http':
                    result = self._call_http_agent(
                        agent_url, 
                        request_body, 
                        headers, 
                        timeout,
                        enable_streaming
                    )
                elif protocol_type == 'grpc':
                    result = self._call_grpc_agent(
                        agent_url, 
                        request_body, 
                        headers, 
                        timeout
                    )
                else:
                    raise AppApiException(500, _('Unsupported protocol type: {protocol}').format(protocol=protocol_type))
                
                # 调用成功，跳出重试循环
                break
                
            except Exception as e:
                last_error = e
                retry_count += 1
                
                if retry_count <= max_retries:
                    # 指数退避重试
                    wait_time = min(2 ** retry_count, 10)
                    time.sleep(wait_time)
                else:
                    # 所有重试都失败，执行降级策略
                    return self._handle_fallback(
                        fallback_strategy, 
                        default_value, 
                        last_error,
                        agent_name
                    )
        
        end_time = time.time()
        response_time = round((end_time - start_time) * 1000, 2)  # 毫秒
        
        # 处理响应数据
        processed_result = self._process_response(result, output_mapping)
        
        return NodeResult(
            {
                'result': processed_result,
                'trace_id': trace_id,
                'response_time': response_time,
                'protocol_type': protocol_type,
                'collaboration_mode': collaboration_mode,
                'agent_name': agent_name,
                'status_code': result.get('code') if isinstance(result, dict) else None,
                'retry_count': retry_count,
            },
            {}
        )

    def _build_request_body(
        self, 
        input_params: Dict[str, Any], 
        context_fields: List[str],
        trace_id: str,
        collaboration_mode: str
    ) -> Dict[str, Any]:
        """
        构建请求体
        
        Args:
            input_params: 输入参数
            context_fields: 上下文字段列表
            trace_id: 追踪ID
            collaboration_mode: 协作模式
            
        Returns:
            构建好的请求体
        """
        # 处理输入参数中的变量引用
        processed_params = {}
        for key, value in input_params.items():
            if isinstance(value, str):
                # 处理模板变量
                processed_params[key] = self.workflow_manage.generate_prompt(value)
            elif isinstance(value, list):
                # 处理引用变量
                processed_params[key] = self._get_reference_content(value)
            else:
                processed_params[key] = value
        
        # 构建上下文信息
        context = {}
        for field in context_fields:
            context[field] = self.workflow_manage.get_reference_field(field, [])
        
        request_body = {
            'trace_id': trace_id,
            'collaboration_mode': collaboration_mode,
            'input_params': processed_params,
            'context': context,
            'timestamp': int(time.time() * 1000),
        }
        
        return request_body

    def _call_http_agent(
        self, 
        url: str, 
        request_body: Dict, 
        headers: Dict[str, str],
        timeout: int,
        enable_streaming: bool = True
    ) -> Dict[str, Any]:
        """
        通过HTTP+SSE调用Agent
        
        Args:
            url: Agent URL
            request_body: 请求体
            headers: 请求头
            timeout: 超时时间
            enable_streaming: 是否启用流式传输
            
        Returns:
            Agent响应
        """
        try:
            if enable_streaming:
                # 流式调用（使用aiohttp）
                return asyncio.run(self._streaming_call(url, request_body, headers, timeout))
            else:
                # 普通HTTP调用
                response = requests.post(
                    url,
                    json=request_body,
                    headers=headers,
                    timeout=timeout
                )
                response.raise_for_status()
                return response.json()
                
        except requests.exceptions.Timeout:
            raise AppApiException(500, _('Agent request timeout after {timeout}s').format(timeout=timeout))
        except requests.exceptions.ConnectionError:
            raise AppApiException(500, _('Failed to connect to agent: {url}').format(url=url))
        except requests.exceptions.HTTPError as e:
            raise AppApiException(500, _('Agent returned error: {error}').format(error=str(e)))

    async def _streaming_call(
        self, 
        url: str, 
        request_body: Dict, 
        headers: Dict[str, str],
        timeout: int
    ) -> Dict[str, Any]:
        """
        流式SSE调用
        
        Args:
            url: Agent URL
            request_body: 请求体
            headers: 请求头
            timeout: 超时时间
            
        Returns:
            聚合后的完整响应
        """
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=request_body,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                if response.status != 200:
                    raise AppApiException(
                        500, 
                        _('Agent returned HTTP {status}: {reason}').format(
                            status=response.status,
                            reason=response.reason
                        )
                    )
                
                # 收集SSE流式数据
                chunks = []
                async for line in response.content:
                    line_str = line.decode('utf-8').strip()
                    if line_str.startswith('data:'):
                        data_str = line_str[5:].strip()
                        if data_str:
                            try:
                                chunk_data = json.loads(data_str)
                                chunks.append(chunk_data)
                            except json.JSONDecodeError:
                                continue
                
                # 返回最后一个完整的响应或聚合结果
                if chunks:
                    return chunks[-1]
                else:
                    return {'code': 200, 'data': '', 'msg': 'success'}

    def _call_grpc_agent(
        self, 
        url: str, 
        request_body: Dict, 
        headers: Dict[str, str],
        timeout: int
    ) -> Dict[str, Any]:
        """
        通过gRPC调用Agent
        
        Args:
            url: gRPC服务端点
            request_body: 请求体
            headers: 请求头
            timeout: 超时时间
            
        Returns:
            Agent响应
        """
        # TODO: 实现gRPC调用
        # 这里需要安装grpcio和相关protobuf定义
        raise AppApiException(
            500, 
            _('gRPC protocol is not yet implemented. Please use HTTP+SSE protocol.')
        )

    def _process_response(
        self, 
        response: Dict[str, Any], 
        output_mapping: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        处理响应数据并应用输出映射
        
        Args:
            response: 原始响应
            output_mapping: 输出字段映射
            
        Returns:
            处理后的响应
        """
        if not isinstance(response, dict):
            return {'raw_response': str(response)}
        
        # 如果定义了输出映射，按照映射提取字段
        if output_mapping:
            mapped_result = {}
            for target_key, source_path in output_mapping.items():
                value = self._extract_nested_value(response, source_path)
                mapped_result[target_key] = value
            return mapped_result
        
        # 否则返回标准格式
        return {
            'code': response.get('code', 200),
            'data': response.get('data'),
            'msg': response.get('msg', 'success'),
            'raw_response': response
        }

    def _extract_nested_value(self, data: Dict, path: str) -> Any:
        """
        从嵌套字典中提取值
        
        Args:
            data: 数据字典
            path: 路径（如 'result.answer'）
            
        Returns:
            提取的值
        """
        keys = path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
            else:
                return None
                
        return current

    def _handle_fallback(
        self,
        fallback_strategy: str,
        default_value: Any,
        error: Exception,
        agent_name: str
    ) -> NodeResult:
        """
        处理降级策略
        
        Args:
            fallback_strategy: 降级策略
            default_value: 默认值
            error: 错误信息
            agent_name: Agent名称
            
        Returns:
            降级结果
        """
        error_msg = str(error)
        
        if fallback_strategy == 'error_message':
            result = {
                'code': 500,
                'data': None,
                'msg': _('Agent {name} call failed: {error}').format(
                    name=agent_name,
                    error=error_msg
                ),
                'fallback': True
            }
        elif fallback_strategy == 'skip':
            result = {
                'code': 200,
                'data': None,
                'msg': _('Agent {name} skipped due to error').format(name=agent_name),
                'fallback': True
            }
        elif fallback_strategy == 'default_value':
            result = {
                'code': 200,
                'data': default_value,
                'msg': _('Using default value due to agent error'),
                'fallback': True
            }
        else:
            result = {
                'code': 500,
                'data': None,
                'msg': error_msg,
                'fallback': True
            }
        
        return NodeResult({'result': result}, {})

    def _get_reference_content(self, fields: List[str]):
        """获取引用变量的内容"""
        return self.workflow_manage.get_reference_field(
            fields[0],
            fields[1:]
        ) if fields else None

    def get_details(self, index: int, **kwargs):
        """获取节点执行详情"""
        return {
            'name': self.node.properties.get('stepName'),
            'index': index,
            'run_time': self.context.get('run_time'),
            'type': self.node.type,
            'status': self.status,
            'err_message': self.err_message,
            'agent_name': self.context.get('agent_name'),
            'protocol_type': self.context.get('protocol_type'),
            'collaboration_mode': self.context.get('collaboration_mode'),
            'response_time': self.context.get('response_time'),
            'status_code': self.context.get('status_code'),
            'retry_count': self.context.get('retry_count', 0),
            'trace_id': self.context.get('trace_id'),
            'result': self.context.get('result'),
            'enableException': self.node.properties.get('enableException'),
        }
