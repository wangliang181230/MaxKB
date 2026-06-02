# MaxKB Logstash 日志集成配置指南

## 概述

MaxKB 支持将日志同时输出到本地文件和 Logstash，方便集中式日志管理和分析。

## 配置方式

### 方式一：通过环境变量配置（推荐）

在 `.env` 文件或 Docker 环境中设置以下环境变量：

```bash
# 启用 Logstash 日志
MAXKB_LOGSTASH_ENABLE=true

# Logstash 主机地址
MAXKB_LOGSTASH_HOST=localhost

# Logstash 端口号
MAXKB_LOGSTASH_PORT=5000

# 协议类型：tcp 或 udp
MAXKB_LOGSTASH_PROTOCOL=tcp

# 消息类型标识
MAXKB_LOGSTASH_MESSAGE_TYPE=maxkb-log

# 标签（逗号分隔）
MAXKB_LOGSTASH_TAGS=maxkb,production

# 额外字段（JSON 格式）
MAXKB_LOGSTASH_EXTRA_FIELDS='{"environment": "production", "service": "maxkb"}'
```

### 方式二：通过 YAML 配置文件

在 `config.yml` 文件中添加以下配置：

```yaml
# Logstash 配置
LOGSTASH_ENABLE: true
LOGSTASH_HOST: localhost
LOGSTASH_PORT: 5000
LOGSTASH_PROTOCOL: tcp  # tcp 或 udp
LOGSTASH_MESSAGE_TYPE: maxkb-log
LOGSTASH_TAGS:
  - maxkb
  - production
LOGSTASH_EXTRA_FIELDS:
  environment: production
  service: maxkb
```

## Logstash 配置示例

### TCP Input 配置

在 Logstash 配置文件中添加 TCP input：

```ruby
input {
  tcp {
    port => 5000
    codec => json_lines
    type => "maxkb-log"
  }
}

filter {
  # 可以根据需要添加过滤器
  if [type] == "maxkb-log" {
    # 添加自定义处理逻辑
    mutate {
      add_field => { "[@metadata][source]" => "maxkb" }
    }
  }
}

output {
  # 输出到 Elasticsearch
  elasticsearch {
    hosts => ["http://localhost:9200"]
    index => "maxkb-logs-%{+YYYY.MM.dd}"
  }
  
  # 或者输出到其他目的地
  # stdout { codec => rubydebug }
}
```

### UDP Input 配置

如果使用 UDP 协议：

```ruby
input {
  udp {
    port => 5000
    codec => json
    type => "maxkb-log"
  }
}
```

## 日志格式

发送到 Logstash 的日志包含以下字段：

```json
{
  "@timestamp": "2026-06-02T12:00:00.000Z",
  "@version": "1",
  "host": "server-name",
  "message": "日志内容",
  "logger_name": "max_kb",
  "log_level": "INFO",
  "log_level_value": 20,
  "pathname": "/path/to/file.py",
  "filename": "file.py",
  "module": "module_name",
  "function": "function_name",
  "line_number": 100,
  "thread": 12345,
  "thread_name": "MainThread",
  "process": 67890,
  "process_name": "MainProcess",
  "type": "maxkb-log",
  "tags": ["maxkb"],
  "environment": "production"
}
```

如果日志包含异常信息，还会添加 `exception` 字段：

```json
{
  "exception": {
    "type": "ValueError",
    "message": "错误信息",
    "stack_trace": ["堆栈跟踪信息"]
  }
}
```

## 使用示例

### Docker Compose 配置

```yaml
version: '3'
services:
  maxkb:
    image: 1panel/maxkb:latest
    environment:
      - MAXKB_CONFIG_TYPE=ENV
      - MAXKB_LOGSTASH_ENABLE=true
      - MAXKB_LOGSTASH_HOST=logstash
      - MAXKB_LOGSTASH_PORT=5000
      - MAXKB_LOGSTASH_PROTOCOL=tcp
    depends_on:
      - logstash
  
  logstash:
    image: docker.elastic.co/logstash/logstash:8.x
    ports:
      - "5000:5000"
    volumes:
      - ./logstash/pipeline:/usr/share/logstash/pipeline
```

### Kibana 查询示例

在 Kibana 中可以使用以下查询：

```kql
# 查询所有 MaxKB 日志
type: "maxkb-log"

# 查询错误日志
type: "maxkb-log" AND log_level: "ERROR"

# 查询特定模块的日志
type: "maxkb-log" AND module: "application"

# 查询包含异常的日志
type: "maxkb-log" AND exception:*
```

## 注意事项

1. **性能考虑**：启用 Logstash 会增加网络开销，建议在生产环境使用 TCP 协议以确保可靠性
2. **连接重试**：如果 Logstash 不可用，系统会自动尝试重新连接，不会影响主程序运行
3. **日志级别**：Logstash handler 使用与文件日志相同的日志级别配置
4. **线程安全**：Logstash handler 实现了线程安全，可以在多线程环境中使用
5. **异常处理**：发送日志到 Logstash 失败不会抛出异常，避免影响业务逻辑

## 故障排查

### 日志未发送到 Logstash

1. 检查环境变量是否正确设置
2. 确认 Logstash 服务是否正常运行
3. 检查网络连接和防火墙设置
4. 查看 MaxKB 启动日志，确认 Logstash 已成功启用

### 连接失败

检查 MaxKB 启动时的输出信息：
- 成功：`Logstash logging enabled: TCP://localhost:5000`
- 失败：`Failed to enable Logstash logging: <错误信息>`

## 更多信息

- Logstash 官方文档：https://www.elastic.co/guide/en/logstash/current/index.html
- Python logging 模块文档：https://docs.python.org/3/library/logging.html
