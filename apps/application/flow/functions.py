# coding=utf-8
"""
    @project: MaxKB
    @Author: wangliang181230
    @file: functions.py
    @date: 2026/7/21 20:38
    @desc: 函数定义，用于增强 `prompt_template.format(context=context, **FUNCS)` 的能力
"""
import json


def py_len(obj):
    try:
        return len(obj)
    except Exception:
        return len(str(obj))


def py_type(obj):
    return type(obj).__name__


def py_isinstance(obj, cls):
    if isinstance(cls, str):
        return type(obj).__name__ == cls
    if isinstance(cls, type):
        return isinstance(obj, cls)
    if isinstance(cls, list):
        type_obj = type(obj)
        return type_obj in cls or type_obj.__name__ in cls
    if isinstance(cls, tuple):
        return isinstance(obj, cls)
    return False


def f_isnull(obj):
    return obj is None


def f_isempty(obj):
    return obj in (None, '', [], {})


def f_clean(obj):
    if isinstance(obj, str):
        return obj.strip()
    if isinstance(obj, list):
        return [f_clean(v) for v in obj if v not in (None, '', [], {})]
    if isinstance(obj, dict):
        return {k: f_clean(v) for k, v in obj.items() if v not in (None, '', [], {})}
    if isinstance(obj, tuple):
        return tuple(f_clean(v) for v in obj if v not in (None, '', [], {}))
    if isinstance(obj, set):
        return set({f_clean(v) for v in obj if v not in (None, '', [], {})})
    return obj


def f_json_dumps(obj):
    return json.dumps(obj, ensure_ascii=False)


FUNCS = {
    # python函数
    "len": py_len,
    "type": py_type,
    "isinstance": py_isinstance,

    # 自定义函数
    "isnull": f_isnull,
    "isempty": f_isempty,
    "clean": f_clean,
    "json_dumps": f_json_dumps,

    # 常量
    "none": None,

    # 工具
    "json": json,

    # 类型
    "int": int,
    "float": float,
    "bool": bool,
    "str": str,
    "tuple": tuple,
    # "None": None,  # 使用None会报错，改为添加小写的 none
    "list": list,
    "set": set,
    "dict": dict,
}
