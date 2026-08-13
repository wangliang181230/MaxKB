# coding=utf-8
"""
    @project: MaxKB
    @Author：虎
    @file： base_function_lib_node.py
    @date：2024/8/8 17:49
    @desc:
"""
import time
from typing import Dict

from django.utils.translation import gettext as _

from application.flow.i_step_node import NodeResult
from application.flow.step_node.tool_node.i_tool_node import IToolNode
from common.utils.common import common_convert_value
from common.utils.tool_code import ToolExecutor

function_executor = ToolExecutor()


def write_context(step_variable: Dict, global_variable: Dict, node, workflow):
    if step_variable is not None:
        for key in step_variable:
            node.context[key] = step_variable[key]
        if workflow.is_result(node, NodeResult(step_variable, global_variable)) and 'result' in step_variable:
            result = str(step_variable['result']) + '\n'
            yield result
            node.answer_text = result
    node.context['run_time'] = time.time() - node.context['start_time']


def convert_value(name: str, value, _type: str, is_required: bool, source, node):
    if value is None and not is_required:
        return None
    if value:
        if source == 'reference' and isinstance(value, list):
            value = node.workflow_manage.get_reference_field(value[0], value[1:])
        elif isinstance(value, str):
            value = node.workflow_manage.generate_field_value(value)
    try:
        value = common_convert_value(_type, value, name)
    except Exception:
        raise Exception(
            _('Field: {name}, Type: {type}, Value: {value}, Type conversion error')
            .format(name=name, type=_type, value=f"${value}({type(value).__name__})")
        )
    if value is None and is_required:
        raise Exception(_(
            'Field: {name}, Type: {_type}, is required'
        ).format(name=name, _type=_type))
    return value


class BaseToolNodeNode(IToolNode):
    def save_context(self, details, workflow_manage):
        self.context['result'] = details.get('result')
        self.context['exception_message'] = details.get('err_message')
        if self.node_params.get('is_result', False):
            self.answer_text = str(details.get('result'))

    def execute(self, input_field_list, code, **kwargs) -> NodeResult:
        params = {field.get('name'): convert_value(field.get('name'), field.get('value'), field.get('type'),
                                                   field.get('is_required'), field.get('source'), self)
                  for field in input_field_list}
        # 合并启动参数默认值（如果有 init_field_list 定义）
        init_field_list = self.node_params.get('init_field_list', [])
        if init_field_list:
            init_params_default_value = {i["field"]: i.get('default_value') for i in init_field_list}
            init_params = kwargs.get('init_params')
            if init_params is not None:
                all_params = init_params_default_value | init_params | params
            else:
                all_params = init_params_default_value | params
        else:
            all_params = params
        result = function_executor.exec_code(code, all_params)
        self.context['params'] = all_params
        return NodeResult({'result': result}, {}, _write_context=write_context)

    def get_details(self, index: int, **kwargs):
        return {
            'name': self.node.properties.get('stepName'),
            "index": index,
            "result": self.context.get('result'),
            "params": self.context.get('params'),
            'run_time': self.context.get('run_time'),
            'type': self.node.type,
            'status': self.status,
            'err_message': self.err_message,
            'enableException': self.node.properties.get('enableException'),
        }
