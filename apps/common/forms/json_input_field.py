# coding=utf-8
"""
    @project: MaxKB
    @Author：虎
    @file： json_input_field.py
    @date：2024/7/11 18:32
    @desc:
"""
from typing import Dict

from common.forms import BaseLabel
from common.forms.base_field import BaseField, TriggerType


class JsonInputField(BaseField):
    """
    JSON 文本框
    """

    def __init__(self, label: str or BaseLabel,
                 required: bool = False,
                 default_value=None,
                 relation_show_field_dict: Dict = None,

                 attrs=None, props_info=None):
        super().__init__('JsonInput', label, required, default_value, relation_show_field_dict,
                         {},
                         TriggerType.OPTION_LIST, attrs, props_info)
