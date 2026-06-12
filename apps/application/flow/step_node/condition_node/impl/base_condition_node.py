# coding=utf-8
"""
    @project: maxkb
    @Author：虎
    @file： base_condition_node.py
    @date：2024/6/7 11:29
    @desc:
"""
from typing import List

from application.flow.i_step_node import NodeResult
from application.flow.compare import _assertion
from application.flow.step_node.condition_node.i_condition_node import IConditionNode


class BaseConditionNode(IConditionNode):
    def save_context(self, details, workflow_manage):
        self.context['branch_id'] = details.get('branch_id')
        self.context['branch_name'] = details.get('branch_name')
        self.context['branch_details'] = details.get('branch_details')
        self.context['exception_message'] = details.get('err_message')

    def execute(self, **kwargs) -> NodeResult:
        branch_list = self.node_params_serializer.data['branch']
        branch, branch_details = self._execute(branch_list)
        r = NodeResult({
            'branch_id': branch.get('id') if branch else None, 
            'branch_name': branch.get('type') if branch else None,
            'branch_details': branch_details
        }, {})
        return r

    def _execute(self, branch_list: List):
        branch_details = []
        for branch in branch_list:
            condition_details = self._evaluate_conditions(branch)
            is_matched = all(cond.get('result', False) for cond in condition_details) if branch.get('condition') == 'and' else any(cond.get('result', False) for cond in condition_details)
            
            branch_details.append({
                'id': branch.get('id'),
                'type': branch.get('type'),
                'condition_logic': branch.get('condition'),
                'is_matched': is_matched,
                'conditions': condition_details
            })
            if is_matched:
                return branch, branch_details
        return None, branch_details

    def _evaluate_conditions(self, branch):
        condition_logic = branch.get('condition')
        condition_list = branch.get('conditions', [])
        condition_details = []

        for condition in condition_list:
            field_list = condition.get('field', [])
            compare = condition.get('compare', '')
            value = condition.get('value', '')

            try:
                field_value = self.workflow_manage.get_reference_field(field_list[0], field_list[1:])
            except Exception:
                field_value = None

            try:
                evaluated_value = self.workflow_manage.generate_prompt(value)
            except Exception:
                evaluated_value = value

            result = _assertion(self.workflow_manage, field_list, compare, value)

            condition_details.append({
                'field': field_list,
                'field_type': type(field_value).__name__ if field_value is not None else None,
                'field_value': field_value,
                'compare': compare,
                'target_type': type(evaluated_value).__name__ if evaluated_value is not None else None,
                'target_value': evaluated_value,
                'result': result
            })

            if (condition_logic == "and" and not result) or (condition_logic == 'or' and result):
                break

        return condition_details

    def get_details(self, index: int, **kwargs):
        return {
            'name': self.node.properties.get('stepName'),
            "index": index,
            'run_time': self.context.get('run_time'),
            'branch_id': self.context.get('branch_id'),
            'branch_name': self.context.get('branch_name'),
            'branch_details': self.context.get('branch_details'),
            'type': self.node.type,
            'status': self.status,
            'err_message': self.err_message,
            'enableException': self.node.properties.get('enableException'),
        }
