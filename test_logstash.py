# -*- coding: utf-8 -*-
"""
Logstash 日志测试脚本
用于测试 Logstash 集成功能
"""
import os
import sys
import django

# 设置 Django 环境
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'apps.maxkb.settings')
django.setup()

import logging

# 获取 logger
logger = logging.getLogger('max_kb')


def test_logstash_logging():
    """测试 Logstash 日志功能"""
    print("=" * 60)
    print("开始测试 Logstash 日志功能")
    print("=" * 60)
    
    # 测试不同级别的日志
    logger.debug("这是一条 DEBUG 级别的测试日志")
    logger.info("这是一条 INFO 级别的测试日志")
    logger.warning("这是一条 WARNING 级别的测试日志")
    logger.error("这是一条 ERROR 级别的测试日志")
    
    # 测试异常日志
    try:
        result = 1 / 0
    except Exception as e:
        logger.exception(f"捕获到异常: {e}")
    
    # 测试带额外信息的日志
    logger.info("用户登录", extra={
        'custom_fields': {
            'user_id': '12345',
            'username': 'test_user',
            'action': 'login'
        }
    })
    
    print("=" * 60)
    print("测试完成！请检查 Logstash 是否收到日志")
    print("=" * 60)


if __name__ == '__main__':
    test_logstash_logging()
