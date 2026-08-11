# coding=utf-8
"""
    @project: maxkb
    @Author：虎
    @file： base_switch_node.py
    @date：2024/6/7 11:29
    @desc:
"""
from typing import List

from application.flow.i_step_node import NodeResult
from application.flow.step_node.switch_node.i_switch_node import ISwitchNode


class BaseSwitchNode(ISwitchNode):
    def save_context(self, details, workflow_manage):
        self.context['branch_id'] = details.get('branch_id')
        self.context['branch_name'] = details.get('branch_name')
        self.context['branch_details'] = details.get('branch_details')
        self.context['exception_message'] = details.get('err_message')

    def execute(self, **kwargs) -> NodeResult:
        field = self.node_params_serializer.data['field']
        branch_list = self.node_params_serializer.data['branch']
        branch, branch_details = self._execute(field, branch_list)
        return NodeResult({
            'branch_id': branch.get('id') if branch else None,
            'branch_name': branch.get('type') if branch else None,
            'branch_details': branch_details,
        }, {})

    def _execute(self, field: List, branch_list: List):
        branch_details = []
        field_value = None
        try:
            field_value = self.workflow_manage.get_reference_field(field[0], field[1:])
        except Exception:
            pass
        field_value = str(field_value) if field_value is not None else None

        for branch in branch_list:
            branch_type = branch.get('type')

            case_value = self.workflow_manage.generate_field_value(str(branch.get('value', '')))
            if isinstance(case_value, str) and case_value.lower().strip() in ('[none]', '[null]', '为空'):
                try:
                    is_matched = True if field_value is None or len(field_value) == 0 else False
                    branch_details.append({
                        'id': branch.get('id'),
                        'type': branch_type,
                        'match_type': '为空',
                        'is_matched': is_matched,
                        'field_value': field_value,
                        'field_type': type(field_value).__name__,
                    })
                    if not is_matched:
                        continue
                    return branch, branch_details
                except TypeError:
                    pass

            # DEFAULT branch always matches last
            if branch_type == 'DEFAULT':
                branch_details.append({
                    'id': branch.get('id'),
                    'type': branch_type,
                    'case_value': case_value,
                    'is_matched': True,
                    'field_value': field_value,
                    'field_type': type(field_value).__name__,
                })
                return branch, branch_details

            is_matched = str(field_value) == str(case_value) if field_value is not None else (case_value == '')
            branch_details.append({
                'id': branch.get('id'),
                'type': branch_type,
                'case_value': case_value,
                'is_matched': is_matched,
                'field_value': field_value,
                'field_type': type(field_value).__name__,
            })
            if is_matched:
                return branch, branch_details

        return None, branch_details

    def get_details(self, index: int, **kwargs):
        return {
            'name': self.node.properties.get('stepName'),
            'index': index,
            'run_time': self.context.get('run_time'),
            'branch_id': self.context.get('branch_id'),
            'branch_name': self.context.get('branch_name'),
            'branch_details': self.context.get('branch_details'),
            'type': self.node.type,
            'status': self.status,
            'err_message': self.err_message,
            'enableException': self.node.properties.get('enableException'),
        }
