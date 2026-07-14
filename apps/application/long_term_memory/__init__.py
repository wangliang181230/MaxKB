import json
import re
from datetime import datetime, timedelta

import uuid_utils.compat as uuid
from django.db.models import Count, QuerySet
from django.utils import timezone
from langchain_core.messages import HumanMessage

from application.models import Chat, ChatRecord, Application, ApplicationLongTermMemory
from common.utils.logger import maxkb_logger
from models_provider.tools import get_model_instance_by_model_workspace_id
from ops import celery_app


# 已存在记忆时，使用此提示模板
long_term_prompt_existing_memory = '''
你是一个专业的用户长期记忆提炼引擎。你的唯一职责是：从对话中精确识别具有持久价值的用户信息，并与已有记忆进行结构化融合，输出供 AI 助手长期使用的用户画像记忆。
核心原则：宁可漏记，不可脑补错记；优先保证记忆真实性，其次追求完备性。

## 输入
【已有记忆】
{{existing_memory}}

【本轮新增对话】
{{new_conversation}}

【当前时间】
{{time}}

---

## 提取门槛（必须同时满足，才可提取）
1. **跨会话复用价值**：这条信息在未来其他对话中仍然适用，而非当次临时需求；
2. **明确可证**：可从对话原文直接支撑，不得推断、脑补、延伸、揣摩潜台词；
3. **个性化增益**：信息属于用户专属特征，记住后能显著区分该用户，让 AI 的回答更贴合；通用常识、大众共识不满足本条。

**以下内容禁止提取：**
- 用户的一次性临时要求、试验性尝试需求（如「这次用表格输出就好，先试一次」）
- 用户提问的具体问题本身（问题不是记忆）
- 无法从对话原文直接证明的推断
- 单次闲聊、问候、感谢、临时瞬时情绪感受等无信息量内容
- AI 的全部回答内容（只提取用户侧信息）
- 普适通用观点、行业基础常识，无用户专属区分度内容

---

## 四类记忆类目区分指南与融合规则

### 【偏好】交互偏好
用户对「AI 如何回应」的稳定倾向，不具备强制约束力。单次偶然表现不判定为稳定偏好；偏好成立优先需要多次对话佐证，除非用户明确声明长期生效。

常见维度：回答详略 / 语言风格（正式/口语）/ 输出格式（表格/列表/段落）/ 是否要举例 / 代码风格偏好 / 回复语言

融合规则：
- 同维度出现新偏好 → **覆盖**旧值，条目末标注 `※已更新`
- 新维度 → 直接追加
- 旧偏好无新证据且未被否定 → **保留**

---

### 【背景】用户背景
用户的客观身份、环境、能力信息、身体状况、个人信息（不要记录姓名、任何卡号或证件号、手机号）等等。

常见维度：职业/角色 / 所在行业 / 技术栈与熟练度 / 使用产品或系统 / 团队规模 / 所在地区 / 疾病症状 / 个人信息

融合规则：
- 与旧记忆事实冲突 → **以新对话为准**，标注 `※已更新`，删除旧值
- 新增独立信息 → 追加
- 信息模糊无法确认 → 追加时标注 `※待确认`
约束：已有确定背景记忆，后续仅模糊表述出现时，**不修改原有确定信息**。

---

### 【约定】明确约定
用户要求AI强制执行/禁止的硬性规则，带有约束指令。

常见维度：禁止行为 / 固定执行动作 / 特定触发词响应 / 内容边界 / 输出限制

融合规则：
- 同类新规则 → **覆盖**旧规则，标注 `※已更新`
- 新增规则 → 追加
- 用户明确取消的规则 → **直接删除**

---

### 【目标】当前目标
用户正在推进的项目、计划、待解决事项。

常见维度：正在进行的项目 / 学习计划 / 待解决的核心问题 / 关键决策

融合规则：
- 已明确完成或放弃的目标 → **删除**
- 新目标 → 追加
- 已有目标有进展更新 → **覆盖**旧描述
约束：短期项目类目标长期无相关对话，存在自然失效倾向。

---

## 通用全局融合规则（全部类目生效）
1. 新增信息与旧记忆语义等价、仅措辞不同：合并精简，不新增重复条目；
2. 同一维度多条信息互为补充，整合为单条存储，禁止碎片化多条并列；
3. 用户主动要求「忘记某信息」，直接删除对应条目；
4. 条目发生修改、覆盖、更新时，统一使用【当前时间】作为本条记录时间；无变更沿用原始时间；
5. `※待确认` 条目后续出现明确事实依据时，移除待确认标记固化信息。

---

## 输出规范
1. **只输出记忆内容本身**，不含任何开头语、解释、总结、额外说明；
2. 四个章节**全部输出**，确无内容写「暂无」，不可省略章节；
3. 每条格式：`- [维度标签] [记忆时间，格式：yyyy-MM-dd HH:mm] 内容`，标签 2~5 字，精准简洁；
4. 带有变更标记（`※已更新` / `※待确认`）的条目置于各章节**最前面**；多条变更条目之间按信息重要程度排序；
5. 优先精炼压缩语句，仅语义完全独立无法合并时才可拆分条目；单条控制在 60 字以内；
6. 输出语言与【本轮新增对话】主要语言保持一致。

---

## 输出格式（注：保留维度标签、时间、标记的中括号 `[]`）

### 【偏好】交互偏好
- [xxx] [yyyy-MM-dd HH:mm] 内容 [※标记]
（暂无则写：暂无）

### 【背景】用户背景
- [xxx] [yyyy-MM-dd HH:mm] 内容 [※标记]
（暂无则写：暂无）

### 【约定】明确约定
- [xxx] [yyyy-MM-dd HH:mm] 内容 [※标记]
（暂无则写：暂无）

### 【目标】当前目标
- [xxx] [yyyy-MM-dd HH:mm] 内容 [※标记]
（暂无则写：暂无）
'''.strip()

# 不存在记忆时，使用此提示模板
long_term_prompt_no_memory = '''
你是一个专业的用户长期记忆提炼引擎。你的唯一职责是：从对话中精确识别具有持久价值的用户信息，输出供 AI 助手长期使用的用户画像记忆。
核心原则：宁可漏记，不可脑补错记；优先保证记忆真实性，其次追求完备性。

## 输入
【本轮对话】
{{new_conversation}}

【当前时间】
{{time}}

---

## 提取门槛（必须同时满足，才可提取）
1. **跨会话复用价值**：这条信息在未来其他对话中仍然适用，而非当次临时需求；
2. **明确可证**：可从对话原文直接支撑，不得推断、脑补、延伸、揣摩潜台词；
3. **个性化增益**：信息属于用户专属特征，记住后能显著区分该用户，让 AI 的回答更贴合；通用常识、大众共识不满足本条。

**以下内容禁止提取：**
- 用户的一次性临时要求、试验性尝试需求（如「这次用表格输出就好，先试一次」）
- 用户提问的具体问题本身（问题不是记忆）
- 无法从对话原文直接证明的推断
- 单次闲聊、问候、感谢、临时瞬时情绪感受等无信息量内容
- AI 的全部回答内容（只提取用户侧信息）
- 普适通用观点、行业基础常识，无用户专属区分度内容

---

## 四类记忆类目区分指南

### 【偏好】交互偏好
用户对「AI 如何回应」的稳定倾向，不具备强制约束力。单次偶然表现不判定为稳定偏好；偏好成立优先需要多次对话佐证，除非用户明确声明长期生效。

常见维度：回答详略 / 语言风格（正式/口语）/ 输出格式（表格/列表/段落）/ 是否要举例 / 代码风格偏好 / 回复语言

---

### 【背景】用户背景
用户的客观身份、环境、能力信息、身体状况、个人信息（不要记录姓名、任何证件号、手机号）等等。

常见维度：职业/角色 / 所在行业 / 技术栈与熟练度 / 使用产品或系统 / 团队规模 / 所在地区 / 疾病症状 / 个人信息

---

### 【约定】明确约定
用户要求AI强制执行/禁止的硬性规则，带有约束指令。

常见维度：禁止行为 / 固定执行动作 / 特定触发词响应 / 内容边界 / 输出限制

---

### 【目标】当前目标
用户正在推进的项目、计划、待解决事项。

常见维度：正在进行的项目 / 学习计划 / 待解决的核心问题 / 关键决策

---

## 输出规范
1. **只输出记忆内容本身**，不含任何开头语、解释、总结、额外说明；
2. 四个章节**全部输出**，确无内容写「暂无」，不可省略章节；
3. 每条格式：`- [维度标签] [记忆时间，格式：yyyy-MM-dd HH:mm] 内容`，标签 2~5 字，精准简洁；
4. 优先精炼压缩语句，仅语义完全独立无法合并时才可拆分条目；单条控制在 60 字以内；
5. 输出语言与【本轮对话】主要语言保持一致。

---

## 输出格式（注：保留维度标签、时间、标记的中括号 `[]`）

### 【偏好】交互偏好
- [xxx] [yyyy-MM-dd HH:mm] 内容
（暂无则写：暂无）

### 【背景】用户背景
- [xxx] [yyyy-MM-dd HH:mm] 内容
（暂无则写：暂无）

### 【约定】明确约定
- [xxx] [yyyy-MM-dd HH:mm] 内容
（暂无则写：暂无）

### 【目标】当前目标
- [xxx] [yyyy-MM-dd HH:mm] 内容
（暂无则写：暂无）
'''.strip()


def _get_long_term_config(application, chat_user_id):
    """
    提取长期记忆配置，返回 dict 或 None（None 表示不需要提取，已清理记忆）
    """
    if application.type == 'WORK_FLOW':
        node_list = application.work_flow.get('nodes', [])
        base_node = next((n for n in node_list if n.get('id') == 'base-node'), None)
        if base_node is None:
            return None
        node_data = base_node.get('properties', {}).get('node_data', {})
        if not node_data.get('long_term_enable', False):
            QuerySet(ApplicationLongTermMemory).filter(
                application_id=application.id, chat_user_id=chat_user_id
            ).delete()
            return None
        return {
            'trigger_type': node_data.get('long_term_trigger_type'),
            'trigger_setting': node_data.get('long_term_trigger_setting') or {'rounds': 10},
            'model_id': node_data.get('long_term_model_id'),
            'model_params': node_data.get('long_term_model_params_setting') or {},
        }
    else:
        if not application.long_term_enable:
            QuerySet(ApplicationLongTermMemory).filter(
                application_id=application.id, chat_user_id=chat_user_id
            ).delete()
            return None
        return {
            'trigger_type': application.long_term_trigger_type,
            'trigger_setting': application.long_term_trigger_setting or {'rounds': 10},
            'model_id': application.long_term_model_id,
            'model_params': application.long_term_model_params_setting or {},
        }


def _get_cron_interval(cron_expression: str):
    """
    通过计算 cron 表达式的连续两次触发时间之差，估算执行间隔。
    返回 timedelta，或 None（无法推断时）。
    """
    from apscheduler.triggers.cron import CronTrigger

    try:
        trigger = CronTrigger.from_crontab(cron_expression.strip())
        now = timezone.now()
        t1 = trigger.get_next_fire_time(None, now)
        if t1 is None:
            return None
        t2 = trigger.get_next_fire_time(t1, t1)
        if t2 is None:
            return None
        return t2 - t1
    except Exception:
        return None


def _get_since_time_from_setting(setting: dict):
    """
    根据定时设置推算本次应提取的对话起始时间。
    返回 datetime（aware），或 None 表示无法推断（回退到 rounds 限制）。
    """
    now = timezone.now()
    schedule_type = setting.get("schedule_type")

    if schedule_type == "daily":
        return now - timedelta(days=1)
    if schedule_type == "weekly":
        return now - timedelta(weeks=1)
    if schedule_type == "monthly":
        return now - timedelta(days=30)
    if schedule_type == "interval":
        unit = (setting.get("interval_unit") or "").strip()
        try:
            value_i = int(setting.get("interval_value"))
            if value_i <= 0:
                return None
        except Exception:
            return None
        delta_map = {
            "seconds": timedelta(seconds=value_i),
            "minutes": timedelta(minutes=value_i),
            "hours": timedelta(hours=value_i),
            "days": timedelta(days=value_i),
        }
        delta = delta_map.get(unit)
        return now - delta if delta else None
    if schedule_type == "cron":
        cron_expression = setting.get("cron_expression") or ""
        delta = _get_cron_interval(cron_expression)
        return now - delta if delta else None
    return None


def _run_extract(workspace_id, application_id, chat_user_id, config, history_limit=None, since_time=None):
    """
    执行一次长期记忆提取。
    - since_time 不为 None 时：提取该时间点之后产生的对话。
    - 否则按 history_limit 条数限制。
    """
    if since_time is None and (history_limit is None or history_limit <= 0):
        return

    qs = (
        QuerySet(ChatRecord)
        .filter(
            chat__application_id=application_id,
            chat__chat_user_id=chat_user_id,
        )
        .order_by('-create_time')
        .only('problem_text', 'answer_text', 'create_time')
    )

    if since_time is not None:
        history_chat_record = list(qs.filter(create_time__gt=since_time))
    else:
        history_chat_record = list(qs[:history_limit])
    if not history_chat_record:
        return

    chat_model = get_model_instance_by_model_workspace_id(
        config['model_id'], workspace_id, **config['model_params']
    )
    if not chat_model:
        return

    long_term_memory = QuerySet(ApplicationLongTermMemory).filter(
        application_id=application_id, chat_user_id=chat_user_id
    ).first()

    existing_memory = long_term_memory.memory if long_term_memory else ''

    # 反转为时间正序（旧→新）
    history_chat_record = list(reversed(history_chat_record))

    new_conversation = json.dumps([
        {
            "用户": record.problem_text,
            "AI": record.answer_text,
        }
        for record in history_chat_record
    ], ensure_ascii=False, indent=4)

    # 区分 `已存在记忆` 和 `不存在记忆`（不存在记忆时，提示词短一些，可减少输入tokens的消耗）
    time = datetime.now().strftime("%Y-%m-%d %H:%M")
    if existing_memory:
        message = long_term_prompt_existing_memory \
            .replace('{{existing_memory}}', existing_memory) \
            .replace('{{new_conversation}}', new_conversation) \
            .replace('{{time}}', time)
    else:
        message = long_term_prompt_no_memory \
            .replace('{{new_conversation}}', new_conversation) \
            .replace('{{time}}', time)

    content_list = []
    for chunk in chat_model.stream([
        HumanMessage(
            content=message
        )
    ]):
        content_list.append(chunk.content)

    content = ''.join(content_list)
    maxkb_logger.info(
        f"执行长期记忆功能：（{'更新' if long_term_memory else '新增'}）\n"
        f"=============== 对话用户ID ===============\n{chat_user_id}\n\n"
        f"=============== 提示词 ===============\n{message}\n\n"
        f"=============== 记忆内容 ===============\n{content}\n\n"
    )
    content = re.sub(r'<think>.*?<\/think>', '', content, flags=re.DOTALL).strip()

    # 获取最新一条对话的时间作为下次提取的起始点
    latest_create_time = max(record.create_time for record in history_chat_record)

    if long_term_memory:
        long_term_memory.memory = content
        long_term_memory.last_extract_time = latest_create_time
        long_term_memory.save()
    else:
        ApplicationLongTermMemory(
            id=uuid.uuid7(),
            application_id=application_id,
            chat_user_id=chat_user_id,
            memory=content,
            last_extract_time=latest_create_time,
        ).save()


def _long_term_job_prefix(application_id) -> str:
    return f"long_term:application:{application_id}:"


def _parse_hhmm(value: str) -> tuple[int, int]:
    hour_str, minute_str = (value or "").split(":")
    hour = int(hour_str)
    minute = int(minute_str)
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError("hour/minute out of range")
    return hour, minute


def _weekday_to_cron(d) -> str:
    mapping = {1: "mon", 2: "tue", 3: "wed", 4: "thu",
               5: "fri", 6: "sat", 7: "sun", 0: "sun"}
    di = int(d)
    if di not in mapping:
        raise ValueError("invalid weekday")
    return mapping[di]


def _remove_long_term_jobs(application_id) -> None:
    from common.job import scheduler

    prefix = _long_term_job_prefix(application_id)
    for job in scheduler.get_jobs():
        if getattr(job, "id", "").startswith(prefix):
            try:
                job.remove()
            except Exception as e:
                maxkb_logger.warning(
                    f"remove long_term job failed, job_id={job.id}, err={e}")


def _execute_scheduled_extract(workspace_id, application_id):
    """
    APScheduler 触发的回调：遍历该应用下所有 chat_user_id，分别投递提取任务。
    """
    application = Application.objects.filter(id=application_id).first()
    if not application:
        _remove_long_term_jobs(application_id)
        return

    chat_user_ids = list(
        QuerySet(Chat).filter(application_id=application_id)
        .exclude(chat_user_id__isnull=True)
        .values_list('chat_user_id', flat=True)
        .distinct()
    )
    for chat_user_id in chat_user_ids:
        config = _get_long_term_config(application, chat_user_id)
        if config is None:
            continue
        if config['trigger_type'] != 'SCHEDULED':
            continue

        # 获取上次提取时间
        long_term_memory = QuerySet(ApplicationLongTermMemory).filter(
            application_id=application_id, chat_user_id=chat_user_id
        ).first()

        setting = config['trigger_setting'] or {}

        # 如果有上次提取时间，则使用该时间；否则根据配置计算初始时间
        if long_term_memory and long_term_memory.last_extract_time:
            since_time = long_term_memory.last_extract_time
            history_limit = None
        else:
            # 首次执行或没有记录，使用配置的时间窗口
            since_time = _get_since_time_from_setting(setting)
            history_limit = None if since_time is not None else setting.get('rounds', 20)

        try:
            _run_extract(workspace_id, application_id, chat_user_id, config,
                         history_limit=history_limit, since_time=since_time)
        except Exception as e:
            maxkb_logger.warning(
                f"scheduled extract long_term_memory failed, "
                f"application_id={application_id}, chat_user_id={chat_user_id}, err={e}"
            )


def _deploy_long_term_daily(workspace_id, application_id, setting):
    from common.job import scheduler

    prefix = _long_term_job_prefix(application_id)
    times = setting.get("time") or []
    for t in times:
        try:
            hour, minute = _parse_hhmm(t)
        except Exception:
            maxkb_logger.warning(
                f"invalid time={t}, application_id={application_id}")
            continue
        job_id = f"{prefix}daily:{hour:02d}{minute:02d}"
        scheduler.add_job(
            _execute_scheduled_extract,
            trigger="cron",
            hour=str(hour),
            minute=str(minute),
            id=job_id,
            kwargs={"workspace_id": workspace_id,
                    "application_id": application_id},
            replace_existing=True,
            misfire_grace_time=60,
            max_instances=1,
        )


def _deploy_long_term_weekly(workspace_id, application_id, setting):
    from common.job import scheduler

    prefix = _long_term_job_prefix(application_id)
    times = setting.get("time") or []
    days = setting.get("days") or []
    if not times or not days:
        maxkb_logger.warning(
            f"empty weekly setting, application_id={application_id}")
        return
    for d in days:
        try:
            dow = _weekday_to_cron(d)
        except Exception:
            maxkb_logger.warning(
                f"invalid weekday={d}, application_id={application_id}")
            continue
        for t in times:
            try:
                hour, minute = _parse_hhmm(t)
            except Exception:
                maxkb_logger.warning(
                    f"invalid time={t}, application_id={application_id}")
                continue
            job_id = f"{prefix}weekly:{dow}:{hour:02d}{minute:02d}"
            scheduler.add_job(
                _execute_scheduled_extract,
                trigger="cron",
                day_of_week=dow,
                hour=str(hour),
                minute=str(minute),
                id=job_id,
                kwargs={"workspace_id": workspace_id,
                        "application_id": application_id},
                replace_existing=True,
                misfire_grace_time=60,
                max_instances=1,
            )


def _deploy_long_term_monthly(workspace_id, application_id, setting):
    from common.job import scheduler

    prefix = _long_term_job_prefix(application_id)
    times = setting.get("time") or []
    days = setting.get("days") or []
    if not times or not days:
        maxkb_logger.warning(
            f"empty monthly setting, application_id={application_id}")
        return
    for d in days:
        try:
            dom = int(d)
            if not (1 <= dom <= 31):
                raise ValueError("invalid day of month")
        except Exception:
            maxkb_logger.warning(
                f"invalid day={d}, application_id={application_id}")
            continue
        for t in times:
            try:
                hour, minute = _parse_hhmm(t)
            except Exception:
                maxkb_logger.warning(
                    f"invalid time={t}, application_id={application_id}")
                continue
            job_id = f"{prefix}monthly:{dom:02d}:{hour:02d}{minute:02d}"
            scheduler.add_job(
                _execute_scheduled_extract,
                trigger="cron",
                day=str(dom),
                hour=str(hour),
                minute=str(minute),
                id=job_id,
                kwargs={"workspace_id": workspace_id,
                        "application_id": application_id},
                replace_existing=True,
                misfire_grace_time=60,
                max_instances=1,
            )


def _deploy_long_term_cron(workspace_id, application_id, setting):
    from apscheduler.triggers.cron import CronTrigger

    from common.job import scheduler

    cron_expression = setting.get('cron_expression')
    if not cron_expression:
        maxkb_logger.warning(
            f"empty cron_expression, application_id={application_id}")
        return
    try:
        cron_trigger = CronTrigger.from_crontab(cron_expression.strip())
    except ValueError:
        maxkb_logger.warning(
            f"invalid cron_expression={cron_expression}, application_id={application_id}")
        return

    job_id = f"{_long_term_job_prefix(application_id)}cron:{cron_expression.strip()}"
    scheduler.add_job(
        _execute_scheduled_extract,
        trigger=cron_trigger,
        id=job_id,
        kwargs={"workspace_id": workspace_id,
                "application_id": application_id},
        replace_existing=True,
        misfire_grace_time=60,
        max_instances=1,
    )


def _deploy_long_term_interval(workspace_id, application_id, setting):
    from common.job import scheduler

    unit = (setting.get("interval_unit") or "").strip()
    value = setting.get("interval_value")
    try:
        value_i = int(value)
        if value_i <= 0:
            raise ValueError("interval_value must be positive")
    except Exception:
        maxkb_logger.warning(
            f"invalid interval_value={value}, application_id={application_id}")
        return
    if unit not in {"seconds", "minutes", "hours", "days"}:
        maxkb_logger.warning(
            f"invalid interval_unit={unit}, application_id={application_id}")
        return

    job_id = f"{_long_term_job_prefix(application_id)}interval:{unit}:{value_i}"
    scheduler.add_job(
        _execute_scheduled_extract,
        trigger="interval",
        id=job_id,
        kwargs={"workspace_id": workspace_id,
                "application_id": application_id},
        replace_existing=True,
        misfire_grace_time=60,
        max_instances=1,
        **{unit: value_i},
    )


@celery_app.task(name="celery:extract_long_term_memory")
def extract_long_term_memory(workspace_id, application_id, chat_user_id):
    application = Application.objects.filter(id=application_id).first()
    if not application:
        return

    config = _get_long_term_config(application, chat_user_id)
    if config is None:
        return

    trigger_type = config['trigger_type']
    trigger_setting = config['trigger_setting']

    if trigger_type != 'ROUND':
        # 按照时间的，定时任务会处理
        return

    rounds = trigger_setting.get('rounds', 10)
    if rounds <= 0:
        return

    current_rounds = QuerySet(ChatRecord).filter(
        chat__application_id=application_id,
        chat__chat_user_id=chat_user_id,
    ).count()
    maxkb_logger.info(f'extract_long_term_memory: current_rounds={current_rounds}, rounds={rounds}')
    if current_rounds % rounds != 0:
        return

    _run_extract(workspace_id, application_id, chat_user_id, config, history_limit=rounds)


@celery_app.task(name="celery:schedule_extract_long_term_memory")
def schedule_extract_long_term_memory(workspace_id, application_id, enabled, trigger_type, trigger_setting):
    # 先清理旧的调度任务
    _remove_long_term_jobs(application_id)

    application = Application.objects.filter(id=application_id).first()
    if not application:
        return

    # 应用关闭长期记忆
    if not enabled:
        QuerySet(ApplicationLongTermMemory).filter(application_id=application_id).delete()
        return
    # 不再是定时触发，则只清理不再部署
    if trigger_type != 'SCHEDULED':
        return

    setting = trigger_setting or {}
    schedule_type = setting.get("schedule_type")

    deployers = {
        "daily": _deploy_long_term_daily,
        "weekly": _deploy_long_term_weekly,
        "monthly": _deploy_long_term_monthly,
        "interval": _deploy_long_term_interval,
        "cron": _deploy_long_term_cron,
    }
    fn = deployers.get(schedule_type)
    if not fn:
        maxkb_logger.warning(f"unsupported long_term schedule_type={schedule_type}, application_id={application_id}")
        return

    fn(workspace_id, application_id, setting)
