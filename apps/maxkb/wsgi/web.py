# coding=utf-8
"""
    @project: MaxKB
    @Author：虎虎
    @file： web.py
    @date：2025/11/5 15:14
    @desc:
"""
import builtins
import csv
import os
import sys

from django.core.wsgi import get_wsgi_application


class TorchBlocker:
    def __init__(self):
        self.original_import = builtins.__import__

    def __call__(self, name, *args, **kwargs):
        if len([True for i in
                ['torch']
                if
                i in name.lower()]) > 0:
            import types
            return types.ModuleType(name)
        else:
            return self.original_import(name, *args, **kwargs)


# 安装导入拦截器
builtins.__import__ = TorchBlocker()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'maxkb.settings')
# 设置 tiktoken 缓存目录：优先使用项目目录下的路径（兼容 Windows 本地开发）
_project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
_tiktoken_cache = os.path.join(_project_dir, 'model', 'tokenizer', 'openai-tiktoken-cl100k-base')
if not os.path.isdir(_tiktoken_cache):
    _docker_cache = '/opt/maxkb-app/model/tokenizer/openai-tiktoken-cl100k-base'
    if os.path.isdir(_docker_cache):
        _tiktoken_cache = _docker_cache
# 确保缓存目录存在，恢复 tiktoken 的落盘缓存，避免每次启动重复联网下载
# 目录只读/权限不足时不应阻断服务启动，降级为无落盘缓存即可
try:
    os.makedirs(_tiktoken_cache, exist_ok=True)
except OSError:
    pass
os.environ['TIKTOKEN_CACHE_DIR'] = _tiktoken_cache

# 缓存缺失时 tiktoken 会通过 urllib 联网下载，Windows 上可能因系统 CA 证书链缺失导致校验失败。
# 此处使用 certifi 提供的 CA 证书包补全校验路径（不关闭 SSL 校验，仅 Windows 生效）。
if sys.platform.startswith('win'):
    try:
        import certifi
        os.environ.setdefault('SSL_CERT_FILE', certifi.where())
        os.environ.setdefault('REQUESTS_CA_BUNDLE', certifi.where())
    except ImportError:
        pass

# Windows 上 C long 为 32 位，sys.maxsize 超出范围会 OverflowError
csv.field_size_limit(2**31 - 1 if sys.platform.startswith('win') else sys.maxsize)
application = get_wsgi_application()


def post_handler():
    from common.database_model_manage.database_model_manage import DatabaseModelManage
    from common import event
    from common.init import init_template
    event.run()
    DatabaseModelManage.init()
    init_template.run()


# 启动后处理函数
post_handler()
