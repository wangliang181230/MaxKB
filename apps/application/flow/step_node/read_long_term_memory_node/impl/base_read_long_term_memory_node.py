# coding=utf-8
"""
    @project: MaxKB
    @Author：AI Assistant
    @file： base_read_long_term_memory_node.py
    @date：2026/07/14
    @desc: 读取长期记忆节点实现
"""
from datetime import datetime, timedelta

from django.db.models import QuerySet

from application.flow.i_step_node import NodeResult
from application.flow.step_node.read_long_term_memory_node.i_read_long_term_memory_node import IReadLongTermMemoryNode
from application.models import ApplicationLongTermMemory, Application
from application.models.application_chat import ChatUserType
from common.utils.common import long_to_uuid
from common.utils.logger import maxkb_logger


class BaseReadLongTermMemoryNode(IReadLongTermMemoryNode):
    """读取长期记忆节点实现类"""

    def save_context(self, details, workflow_manage):
        """保存上下文"""
        self.context["memories"] = details.get("memories", "")
        self.context["total_count"] = details.get("total_count", "")
        self.context["chat_user_id"] = details.get("chat_user_id")
        self.context["chat_user_type"] = details.get("chat_user_type", "")
        self.context["application_ids"] = details.get("application_ids", [])
        self.context["application_list"] = details.get("application_list", [])
        self.context["days"] = details.get("days", 0)
        self.context["run_time"] = details.get("run_time")
        self.context["err_message"] = details.get("err_message")
        self.context["exception_message"] = details.get("err_message")

    def execute(self, chat_user_id, chat_user_type, application_ids, days=0, **kwargs) -> NodeResult:
        """
        执行读取长期记忆

        Args:
            chat_user_id: 对话用户ID
            chat_user_type: 对话用户类型
            application_ids: 开启了长期记忆功能的高级智能体ID列表（可选，为空时查询所有启用了长期记忆的应用）
            days: 查询天数（可选，为0时不限制，大于0时只查询最近N天更新的数据）

        Returns:
            NodeResult: 包含读取到的长期记忆数据
        """
        application_list = []

        try:
            if chat_user_type and chat_user_type != ChatUserType.CHAT_USER.value:
                maxkb_logger.info(
                    f"跳过读取长期记忆：chat_user_id={chat_user_id}, chat_user_type={chat_user_type}({type(chat_user_type)}) 不是对话用户"
                )
                return NodeResult({
                    "err_message": f"对话用户类型为：{chat_user_type}，不是对话用户（CHAT_USER）",
                    "chat_user_id": chat_user_id,
                    "chat_user_type": chat_user_type,
                    "application_ids": application_ids,
                    "application_list": application_list,
                    "days": days,
                }, {})

            # 如果 chat_user_id 是 业务系统的Long型ID，则转换为UUID
            if isinstance(chat_user_id, str) and chat_user_id.isdigit():
                chat_user_id = int(chat_user_id)
            if isinstance(chat_user_id, int):
                chat_user_id = long_to_uuid(chat_user_id)

            # 查询长期记忆数据
            qs = QuerySet(ApplicationLongTermMemory).filter(chat_user_id=chat_user_id)
            if application_ids:
                qs = qs.filter(application_id__in=application_ids)
                applications = QuerySet(Application).filter(id__in=application_ids).only("id", "name")
                application_list = [{"id": str(app.id), "name": app.name} for app in applications]
            if days and days > 0:
                cutoff_date = datetime.now() - timedelta(days=float(days))
                qs = qs.filter(update_time__gte=cutoff_date)
            long_term_memories = qs.only("memory")

            # 构建返回结果
            memories = []
            for idx, memory_record in enumerate(list(long_term_memories)):
                memories.append(
                    f"### 长期记忆 {idx + 1}：\n"
                    f"{memory_record.memory.replace('### ', '#### ')}"
                )

            maxkb_logger.info(
                f"成功读取长期记忆：chat_user_id={chat_user_id}, "
                f"chat_user_type={chat_user_type}, "
                f"application_ids={application_ids}, "
                f"days={days}, "
                f"memory_count={len(memories)}"
            )

            return NodeResult({
                "memories": "\n\n".join(memories).strip() if memories else "暂无",
                "total_count": len(memories),
                "chat_user_id": chat_user_id,
                "chat_user_type": chat_user_type,
                "application_ids": application_ids,
                "application_list": application_list,
                "days": days,
            }, {})

        except Exception as e:
            maxkb_logger.error(f"读取长期记忆异常：{str(e)}", exc_info=True)
            return NodeResult({
                "err_message": f"读取长期记忆失败：{str(e)}",
                "chat_user_id": chat_user_id,
                "chat_user_type": chat_user_type,
                "application_ids": application_ids,
                "application_list": application_list,
                "days": days,
            }, {})

    def get_details(self, index: int, **kwargs):
        """获取节点执行详情"""
        return {
            "name": self.node.properties.get("stepName"),
            "index": index,
            "run_time": self.context.get("run_time"),
            "type": self.node.type,
            "status": self.status,
            "err_message": self.context.get("err_message"),
            "enableException": self.node.properties.get("enableException"),
            "chat_user_id": self.context.get("chat_user_id"),
            "chat_user_type": self.context.get("chat_user_type", ""),
            "application_ids": self.context.get("application_ids", []),
            "application_list": self.context.get("application_list", []),
            "days": self.context.get("days", 0),
            "memories": self.context.get("memories", ""),
            "total_count": self.context.get("total_count", ""),
        }