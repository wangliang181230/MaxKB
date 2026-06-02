# -*- coding: utf-8 -*-
"""
Logstash 日志处理器
用于将日志发送到 Logstash
"""
import json
import logging
import socket
import threading
from datetime import datetime, timezone


class LogstashHandler(logging.Handler):
    """
    Logstash TCP Handler
    通过 TCP 连接将日志发送到 Logstash
    """
    
    def __init__(self, host='localhost', port=5000, message_type='maxkb-log', 
                 tags=None, fqdn=False, extra_fields=None):
        """
        初始化 Logstash Handler
        
        :param host: Logstash 主机地址
        :param port: Logstash 端口号
        :param message_type: 消息类型标识
        :param tags: 标签列表
        :param fqdn: 是否使用完全限定域名
        :param extra_fields: 额外字段字典
        """
        super().__init__()
        self.host = host
        self.port = port
        self.message_type = message_type
        self.tags = tags or []
        self.fqdn = fqdn
        self.extra_fields = extra_fields or {}
        
        # 创建 TCP 连接
        self.sock = None
        self._connect()
        
        # 线程锁确保线程安全
        self.lock = threading.Lock()

    def _connect(self):
        """建立 TCP 连接到 Logstash"""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
        except Exception as e:
            print(f"Failed to connect to Logstash: {e}")
            self.sock = None

    def close(self):
        """关闭连接"""
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
        super().close()

    def emit(self, record):
        """发送日志记录到 Logstash"""
        try:
            with self.lock:
                # 如果连接断开，尝试重新连接
                if not self.sock:
                    self._connect()
                
                if not self.sock:
                    return
                
                # 格式化日志消息
                message = self.format_record(record)
                
                # 发送消息（添加换行符作为分隔符）
                data = (json.dumps(message) + '\n').encode('utf-8')
                self.sock.sendall(data)
                
        except Exception as e:
            # 连接失败时关闭连接，下次会重新连接
            if self.sock:
                try:
                    self.sock.close()
                except Exception:
                    pass
                self.sock = None
            # 不抛出异常，避免影响主程序
            self.handleError(record)

    def format_record(self, record):
        """格式化日志记录为 Logstash 兼容的 JSON 格式"""
        # 获取主机名
        if self.fqdn:
            hostname = socket.getfqdn()
        else:
            hostname = socket.gethostname()
        
        # 构建基础消息
        message = {
            '@timestamp': datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            '@version': '1',
            'host': hostname,
            'message': record.getMessage(),
            'logger_name': record.name,
            'log_level': record.levelname,
            'log_level_value': record.levelno,
            'pathname': record.pathname,
            'filename': record.filename,
            'module': record.module,
            'function': record.funcName,
            'line_number': record.lineno,
            'thread': record.thread,
            'thread_name': record.threadName,
            'process': record.process,
            'process_name': record.processName,
            'type': self.message_type,
        }
        
        # 添加标签
        if self.tags:
            message['tags'] = self.tags
        
        # 添加额外字段
        if self.extra_fields:
            message.update(self.extra_fields)
        
        # 如果有异常信息，添加异常堆栈
        if record.exc_info and record.exc_info[0] is not None:
            import traceback
            message['exception'] = {
                'type': str(record.exc_info[0].__name__),
                'message': str(record.exc_info[1]),
                'stack_trace': traceback.format_exception(*record.exc_info)
            }
        
        # 添加自定义字段
        if hasattr(record, 'custom_fields'):
            message.update(record.custom_fields)
        
        return message


class LogstashUDPHandler(LogstashHandler):
    """
    Logstash UDP Handler
    通过 UDP 连接将日志发送到 Logstash
    """
    
    def _connect(self):
        """建立 UDP 连接到 Logstash"""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        except Exception as e:
            print(f"Failed to create UDP socket: {e}")
            self.sock = None

    def emit(self, record):
        """发送日志记录到 Logstash (UDP)"""
        try:
            with self.lock:
                # 如果连接未建立，尝试建立
                if not self.sock:
                    self._connect()
                
                if not self.sock:
                    return
                
                # 格式化日志消息
                message = self.format_record(record)
                
                # 发送消息（UDP 不需要换行符）
                data = json.dumps(message).encode('utf-8')
                self.sock.sendto(data, (self.host, self.port))
                
        except Exception as e:
            if self.sock:
                try:
                    self.sock.close()
                except Exception:
                    pass
                self.sock = None
            self.handleError(record)