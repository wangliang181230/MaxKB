# -*- coding: utf-8 -*-
#
import logging
import os

from ..const import PROJECT_DIR, CONFIG, LOG_DIR

MAX_KB_LOG_FILE = os.path.join(LOG_DIR, 'maxkb.log')
DRF_EXCEPTION_LOG_FILE = os.path.join(LOG_DIR, 'drf_exception.log')
UNEXPECTED_EXCEPTION_LOG_FILE = os.path.join(LOG_DIR, 'unexpected_exception.log')
LOG_LEVEL = CONFIG.get_log_level()

# Logstash 配置
LOGSTASH_ENABLE = CONFIG.get('LOGSTASH_ENABLE', False)
LOGSTASH_HOST = CONFIG.get('LOGSTASH_HOST', 'localhost')
LOGSTASH_PORT = CONFIG.get('LOGSTASH_PORT', 5000)
LOGSTASH_PROTOCOL = CONFIG.get('LOGSTASH_PROTOCOL', 'tcp')  # tcp or udp
LOGSTASH_MESSAGE_TYPE = CONFIG.get('LOGSTASH_MESSAGE_TYPE', 'maxkb-log')
LOGSTASH_TAGS = CONFIG.get('LOGSTASH_TAGS', ['maxkb'])
LOGSTASH_EXTRA_FIELDS = CONFIG.get('LOGSTASH_EXTRA_FIELDS', {})

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'main': {
            'datefmt': '%Y-%m-%d %H:%M:%S',
            'format': '%(asctime)s [%(module)s %(levelname)s] %(message)s',
        },
        'exception': {
            'datefmt': '%Y-%m-%d %H:%M:%S',
            'format': '\n%(asctime)s [%(levelname)s] %(message)s',
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
        'syslog': {
            'format': 'maxkb: %(message)s'
        },
        'msg': {
            'format': '%(message)s'
        }
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'main'
        },
        'file': {
            'encoding': 'utf8',
            'level': 'DEBUG',
            'class': 'common.utils.logger.DailyTimedRotatingFileHandler',
            'when': 'midnight',
            'interval': 1,
            'backupCount': 7,
            'formatter': 'main',
            'filename': MAX_KB_LOG_FILE,
        },
        'drf_exception': {
            'encoding': 'utf8',
            'level': 'DEBUG',
            'class': 'common.utils.logger.DailyTimedRotatingFileHandler',
            'formatter': 'exception',
            'when': 'midnight',
            'interval': 1,
            'backupCount': 7,
            'filename': DRF_EXCEPTION_LOG_FILE,
        },
        'unexpected_exception': {
            'encoding': 'utf8',
            'level': 'DEBUG',
            'class': 'common.utils.logger.DailyTimedRotatingFileHandler',
            'when': 'midnight',
            'interval': 1,
            'backupCount': 7,
            'formatter': 'exception',
            'filename': UNEXPECTED_EXCEPTION_LOG_FILE,
        },
        'syslog': {
            'level': 'INFO',
            'class': 'logging.NullHandler',
            'formatter': 'syslog'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['null'],
            'propagate': False,
            'level': LOG_LEVEL,
        },
        'django.request': {
            'handlers': ['console', 'file', 'syslog'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'sqlalchemy': {
            'handlers': ['console', 'file', 'syslog'],
            'level': "ERROR",
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console', 'file', 'syslog'],
            'propagate': False,
            'level': LOG_LEVEL,
        },
        'django.server': {
            'handlers': ['console', 'file', 'syslog'],
            'level': 'ERROR',
            'propagate': False,
        },
        'max_kb': {
            'handlers': ['console', 'file'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'common.event': {
            'handlers': ['console', 'file'],
            'level': "DEBUG",
            'propagate': False,
        },
    }
}

# 如果启用了 Logstash，动态添加 Logstash handler
if LOGSTASH_ENABLE:
    try:
        from apps.common.utils.logstash_handler import LogstashHandler, LogstashUDPHandler
        
        # 根据协议选择 Handler 类
        if LOGSTASH_PROTOCOL.lower() == 'udp':
            logstash_handler_class = LogstashUDPHandler
        else:
            logstash_handler_class = LogstashHandler
        
        # 创建 Logstash handler 实例
        logstash_handler = logstash_handler_class(
            host=LOGSTASH_HOST,
            port=int(LOGSTASH_PORT),
            message_type=LOGSTASH_MESSAGE_TYPE,
            tags=LOGSTASH_TAGS if isinstance(LOGSTASH_TAGS, list) else [LOGSTASH_TAGS],
            extra_fields=LOGSTASH_EXTRA_FIELDS if isinstance(LOGSTASH_EXTRA_FIELDS, dict) else {}
        )
        logstash_handler.setLevel(LOG_LEVEL)
        logstash_handler.setFormatter(logging.Formatter('%(message)s'))
        
        # 将 logstash handler 添加到 handlers 配置中
        LOGGING['handlers']['logstash'] = {
            '()': lambda: logstash_handler,
            'level': LOG_LEVEL,
        }
        
        # 为所有 logger 添加 logstash handler
        for logger_name in LOGGING['loggers']:
            if 'handlers' in LOGGING['loggers'][logger_name]:
                LOGGING['loggers'][logger_name]['handlers'].append('logstash')
        
        print(f"Logstash logging enabled: {LOGSTASH_PROTOCOL.upper()}://{LOGSTASH_HOST}:{LOGSTASH_PORT}")
    except Exception as e:
        print(f"Failed to enable Logstash logging: {e}")

SYSLOG_ENABLE = CONFIG.SYSLOG_ENABLE

if not os.path.isdir(LOG_DIR):
    os.makedirs(LOG_DIR, mode=0o700, exist_ok=True)
