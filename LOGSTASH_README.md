# MaxKB Logstash 集成 - 快速开始

## 📋 概述

本实现为 MaxKB 添加了将日志同时发送到 Logstash 的功能，支持集中式日志管理和分析。

## ✨ 功能特性

- ✅ 支持 TCP 和 UDP 协议
- ✅ 自动重连机制
- ✅ 线程安全
- ✅ 完整的异常信息捕获
- ✅ 可自定义标签和额外字段
- ✅ 兼容 ELK Stack (Elasticsearch, Logstash, Kibana)

## 🚀 快速开始

### 1. 启用 Logstash 日志

#### 方式一：环境变量（推荐）

```bash
# 在 .env 文件或 Docker 环境中设置
MAXKB_LOGSTASH_ENABLE=true
MAXKB_LOGSTASH_HOST=localhost
MAXKB_LOGSTASH_PORT=5000
MAXKB_LOGSTASH_PROTOCOL=tcp
```

#### 方式二：YAML 配置文件

在 `config.yml` 中添加：

```yaml
LOGSTASH_ENABLE: true
LOGSTASH_HOST: localhost
LOGSTASH_PORT: 5000
LOGSTASH_PROTOCOL: tcp
```

### 2. 配置 Logstash

使用提供的示例配置文件 [logstash-example.conf](logstash-example.conf)：

```bash
# 复制配置文件到 Logstash pipeline 目录
cp logstash-example.conf /etc/logstash/conf.d/

# 重启 Logstash
systemctl restart logstash
```

### 3. 测试功能

运行测试脚本验证配置：

```bash
python test_logstash.py
```

## 📁 文件说明

| 文件 | 说明 |
|------|------|
| `apps/common/utils/logstash_handler.py` | Logstash 日志处理器实现 |
| `apps/maxkb/settings/logging.py` | 日志配置文件（已修改） |
| `apps/maxkb/conf.py` | 配置文件（已添加 Logstash 配置项） |
| `logstash-example.conf` | Logstash 配置示例 |
| `docker-compose-logstash.yml` | Docker Compose 完整部署示例 |
| `test_logstash.py` | 测试脚本 |
| `LOGSTASH_CONFIG_GUIDE.md` | 详细配置指南 |

## 🔧 配置选项

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| LOGSTASH_ENABLE | false | 是否启用 Logstash |
| LOGSTASH_HOST | localhost | Logstash 主机地址 |
| LOGSTASH_PORT | 5000 | Logstash 端口号 |
| LOGSTASH_PROTOCOL | tcp | 协议类型 (tcp/udp) |
| LOGSTASH_MESSAGE_TYPE | maxkb-log | 消息类型标识 |
| LOGSTASH_TAGS | ['maxkb'] | 标签列表 |
| LOGSTASH_EXTRA_FIELDS | {} | 额外字段 |

## 🐳 Docker Compose 部署

使用提供的完整部署示例：

```bash
# 启动所有服务（MaxKB + Logstash + Elasticsearch + Kibana）
docker-compose -f docker-compose-logstash.yml up -d

# 查看日志
docker-compose -f docker-compose-logstash.yml logs -f maxkb

# 访问 Kibana
# http://localhost:5601
```

## 📊 在 Kibana 中查看日志

1. 打开 Kibana: http://localhost:5601
2. 创建索引模式: `maxkb-logs-*`
3. 使用以下查询过滤日志:

```kql
# 所有 MaxKB 日志
type: "maxkb-log"

# 错误日志
type: "maxkb-log" AND log_level: "ERROR"

# 特定模块
type: "maxkb-log" AND module: "application"

# 包含异常的日志
type: "maxkb-log" AND exception:*
```

## 🔍 日志格式

发送到 Logstash 的日志包含以下字段：

```json
{
  "@timestamp": "2026-06-02T12:00:00.000Z",
  "@version": "1",
  "host": "server-name",
  "message": "日志内容",
  "logger_name": "max_kb",
  "log_level": "INFO",
  "module": "application",
  "function": "my_function",
  "line_number": 100,
  "type": "maxkb-log",
  "tags": ["maxkb"]
}
```

## ⚠️ 注意事项

1. **性能影响**: 启用 Logstash 会增加网络开销，建议在生产环境使用 TCP 协议
2. **连接重试**: 如果 Logstash 不可用，系统会自动重试，不影响主程序
3. **日志级别**: Logstash 使用与文件日志相同的日志级别
4. **线程安全**: 已实现线程安全，可在多线程环境使用

## 🐛 故障排查

### 问题：日志未发送到 Logstash

**解决方案：**
1. 检查环境变量是否正确设置
2. 确认 Logstash 服务正在运行
3. 检查网络连接和防火墙
4. 查看 MaxKB 启动日志

### 问题：连接失败

**检查启动输出：**
- 成功：`Logstash logging enabled: TCP://localhost:5000`
- 失败：`Failed to enable Logstash logging: <错误信息>`

## 📚 更多信息

- [详细配置指南](LOGSTASH_CONFIG_GUIDE.md)
- [Logstash 官方文档](https://www.elastic.co/guide/en/logstash/current/index.html)
- [Python logging 文档](https://docs.python.org/3/library/logging.html)

## 🤝 贡献

如有问题或建议，请提交 Issue 或 Pull Request。
