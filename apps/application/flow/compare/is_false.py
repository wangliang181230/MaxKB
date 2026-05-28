# coding=utf-8
"""
    @project: MaxKB
    @Author：虎
    @file： is_false.py
    @date：2026/5/18 13:48
    @desc: 为假比较器
"""
from .compare import Compare


class IsFalseCompare(Compare):

    def compare(self, source_value, compare, target_value):
        return source_value in (False, 'False', 'false', 0, '0')
