# coding=utf-8
"""
    @project: MaxKB
    @Author：AI Assistant
    @file： base_read_chat_history_node.py
    @date：2026/08/06
    @desc: 读取历史对话节点实现
"""
from django.db.models import QuerySet

from application.flow.i_step_node import NodeResult
from application.flow.step_node.read_chat_history_node.i_read_chat_history_node import IReadChatHistoryNode
from application.models import Application, Chat, ChatRecord
from common.utils.logger import maxkb_logger


class BaseReadChatHistoryNode(IReadChatHistoryNode):
    """读取历史对话节点实现类"""

    def save_context(self, details, workflow_manage):
        """保存上下文"""
        self.context["chat_id"] = details.get("chat_id")
        self.context["application"] = details.get("application")
        self.context["chat"] = details.get("chat")
        self.context["history_list"] = details.get("history_list", [])
        self.context["total_count"] = details.get("total_count", 0)
        self.context["err_message"] = details.get("err_message")
        self.context["exception_message"] = details.get("err_message")

    def execute(self, chat_id, **kwargs) -> NodeResult:
        """
        执行读取历史对话

        Args:
            chat_id: 对话ID，可以是其他智能体的，也可以是当前智能体的

        Returns:
            NodeResult: 包含读取到的历史对话数据
        """
        application = None
        chat = None
        history_list = []
        total_count = 0

        try:
            if not chat_id:
                maxkb_logger.warning("读取历史对话：chat_id 为空")
                return NodeResult({
                    "err_message": "对话ID不能为空",
                    "chat_id": chat_id,
                    "application": None,
                    "chat": None,
                    "history_list": [],
                    "total_count": 0,
                }, {})

            # 查询对话信息
            chat = QuerySet(Chat).filter(id=chat_id, is_deleted=False).first()
            if chat is None:
                maxkb_logger.warning(f"读取历史对话：对话不存在，chat_id={chat_id}")
                return NodeResult({
                    "err_message": f"对话 {chat_id} 不存在",
                    "chat_id": chat_id,
                    "application": None,
                    "chat": None,
                    "history_list": [],
                    "total_count": 0,
                }, {})
            application_id = str(chat.application_id)
            chat = {
                "id": str(chat.id),
                "application_id": application_id,
                "chat_user_id": chat.chat_user_id,
                "chat_user_type": chat.chat_user_type,
                "chat_record_count": chat.chat_record_count,
                "source": chat.source,
                "ip_address": chat.ip_address,
                "create_time": chat.create_time.isoformat() if chat.create_time else None,
            }

            # 查询智能体信息
            application = QuerySet(Application).filter(id=application_id).first()
            if application:
                application = {
                    "id": str(application.id),
                    "name": application.name,
                }
            else:
                application = {
                    "id": application_id,
                    "name": "智能体数据不存在",
                    "deleted": True,
                }

            # 查询该对话的所有历史对话记录
            chat_records = QuerySet(ChatRecord).filter(chat_id=chat_id).order_by('index', 'create_time')
            total_count = chat_records.count()

            # 构建历史对话列表
            for record in chat_records:
                history_list.append({
                    # "id": str(record.id),
                    # "index": record.index,
                    "problem_text": record.problem_text,
                    "answer_text": record.answer_text,
                    # "message_tokens": record.message_tokens,
                    # "answer_tokens": record.answer_tokens,
                    # "run_time": record.run_time,
                    # "create_time": record.create_time.isoformat() if record.create_time else None,
                })

            maxkb_logger.info(
                f"成功读取历史对话：chat_id={chat_id}, "
                f"application_id={application_id}, "
                f"record_count={total_count}"
            )

            return NodeResult({
                "chat_id": chat_id,
                "application": application,
                "chat": chat,
                "history_list": history_list,
                "total_count": total_count,
            }, {})

        except Exception as e:
            maxkb_logger.error(f"读取历史对话异常：{str(e)}", exc_info=True)
            return NodeResult({
                "err_message": f"读取历史对话失败：{str(e)}",
                "chat_id": chat_id,
                "application": application,
                "chat": chat,
                "history_list": history_list,
                "total_count": total_count,
            }, {})

    def get_details(self, index: int, **kwargs):
        """获取节点执行详情"""
        return {
            "name": self.node.properties.get("stepName"),
            "index": index,
            "type": self.node.type,
            "status": self.status,
            "err_message": self.context.get("err_message"),
            "enableException": self.node.properties.get("enableException"),
            "chat_id": self.context.get("chat_id"),
            "application": self.context.get("application"),
            "chat": self.context.get("chat"),
            "history_list": self.context.get("history_list", []),
            "history_text": self.context.get("history_text", ""),
            "total_count": self.context.get("total_count", 0),
        }
