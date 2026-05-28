# coding=utf-8
"""
    @project: MaxKB
    @Author：虎
    @file： is_not_false.py
    @date：2026/5/18 13:48
    @desc: 不为假比较器
"""
from .compare import Compare


class IsNotFalseCompare(Compare):

    def compare(self, source_value, compare, target_value):
        return source_value not in (False, 'False', 'false', 0, '0')
