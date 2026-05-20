# coding=utf-8
import io

import uuid_utils.compat as uuid
from django.db.models import QuerySet

from application.flow.common import WorkflowMode
from application.flow.i_step_node import NodeResult
from application.flow.step_node.document_extract_node.i_document_extract_node import IDocumentExtractNode
from common.utils.common import get_file_name_from_url_or_response, normalize_uuid
from common.utils.logger import maxkb_logger
from knowledge.models import File, FileSourceType
from knowledge.serializers.document import split_handles, parse_table_handle_list, FileBufferHandle
from oss.serializers.file import fetch_file_from_url, get_application_file_limit_bytes

splitter = '\n`-----------------------------------`\n'
# 从 URL 下载文档的体积硬上限（防止远端无长度响应打满进程内存）
DOWNLOAD_FILE_LIMIT = 100 * 1024 * 1024


class BaseDocumentExtractNode(IDocumentExtractNode):
    def save_context(self, details, workflow_manage):
        self.context['content'] = details.get('content')
        self.context['exception_message'] = details.get('err_message')

    def execute(self, document, chat_id=None, **kwargs):
        get_buffer = FileBufferHandle().get_buffer

        self.context['document_list'] = document
        if document is None or not isinstance(document, list):
            return NodeResult({'content': '', 'document_list': []}, {})

        # 安全获取 application
        application_id = None
        tool_id = None
        knowledge_id = None
        if [WorkflowMode.KNOWLEDGE, WorkflowMode.KNOWLEDGE_LOOP].__contains__(self.workflow_manage.flow.workflow_mode):
            knowledge_id = self.workflow_params.get('knowledge_id')
        elif [WorkflowMode.APPLICATION, WorkflowMode.APPLICATION_LOOP].__contains__(
                self.workflow_manage.flow.workflow_mode):
            application_id = self.workflow_manage.work_flow_post_handler.chat_info.application_id
        elif [WorkflowMode.TOOL, WorkflowMode.TOOL_LOOP].__contains__(self.workflow_manage.flow.workflow_mode):
            tool_id = self.workflow_params.get('tool_id')

        # 下载体积上限：应用模式沿用应用配置的上传上限（并与硬上限取小），其余场景使用硬上限
        download_file_limit = (min(get_application_file_limit_bytes(application_id), DOWNLOAD_FILE_LIMIT)
                               if application_id else DOWNLOAD_FILE_LIMIT)

        # 提取并保存成功的图片列表，用于节点输出
        extracted_image_list = []

        # 文档文件中提取到的图片保存
        def save_image(image_list):
            if not image_list:
                return
            # 一次性查询已存在的文件，避免循环内逐个 exists 查询（N+1）
            image_file_id_list = [str(image.id) for image in image_list if image.id]
            existing_file_id_set = set(
                map(str, QuerySet(File).filter(id__in=image_file_id_list).values_list('id', flat=True))
            ) if image_file_id_list else set()
            for image in image_list:
                meta = {
                    'debug': False if (application_id or knowledge_id or tool_id) else True,
                    'chat_id': chat_id,
                    'application_id': str(application_id) if application_id else None,
                    'knowledge_id': str(knowledge_id) if knowledge_id else None,
                    'tool_id': str(tool_id) if tool_id else None,
                    'file_id': str(image.id) if image.id else None
                }
                file_bytes = image.meta.pop('content')
                new_file = File(
                    id=meta['file_id'],
                    file_name=image.file_name,
                    file_size=len(file_bytes),
                    source_type=FileSourceType.APPLICATION.value if application_id else FileSourceType.KNOWLEDGE.value if knowledge_id else FileSourceType.TOOL.value,
                    source_id=application_id or knowledge_id or tool_id,
                    meta=meta
                )
                if str(new_file.id) not in existing_file_id_set:
                    new_file.save(file_bytes)

                extracted_image_list.append({
                    "name": image.file_name,
                    "size": new_file.file_size,
                    "url": f"./oss/file/{new_file.id}",
                    "file_id": new_file.id,
                })

        # 从URL下载文件并保存为File对象
        def download_and_save_file(url, file_name=None):
            try:
                # 安全下载：会话级适配器在连接前校验解析的 IP（防 DNS 重绑定）+ 流式读取硬上限
                file_bytes, final_url, response_headers = fetch_file_from_url(
                    url,
                    file_limit=download_file_limit,
                    max_redirects=5,
                    connect_timeout=10,
                    read_timeout=60,
                )

                # 获取文件名（如果未提供）：以最终地址为准（跳转后地址的文件名/类型可能与原始地址不同）
                if not file_name:
                    # 从 `响应头 Content-Disposition`、`url` 中获取文件名
                    # 从 `bytes` 或 `响应头 Content-Type` 中获取文件类型
                    file_name = get_file_name_from_url_or_response(
                        final_url, None, "downloaded_document",
                        file_bytes=file_bytes, headers=response_headers,
                    )

                # 生成文件ID
                file_id = uuid.uuid7()

                # 确定source_type和source_id
                if application_id:
                    source_type = FileSourceType.APPLICATION.value
                elif knowledge_id:
                    source_type = FileSourceType.KNOWLEDGE.value
                else:
                    source_type = FileSourceType.TOOL.value
                source_id = application_id or knowledge_id or tool_id

                # 创建File对象
                meta = {
                    'debug': False if (application_id or knowledge_id or tool_id) else True,
                    'chat_id': chat_id,
                    'application_id': str(application_id) if application_id else None,
                    'knowledge_id': str(knowledge_id) if knowledge_id else None,
                    'tool_id': str(tool_id) if tool_id else None,
                    'file_id': str(file_id),
                    'source_url': url
                }
                new_file = File(
                    id=file_id,
                    file_name=file_name,
                    file_size=len(file_bytes),
                    source_type=source_type,
                    source_id=source_id,
                    meta=meta
                )

                # 保存文件到数据库
                new_file.save(file_bytes)

                maxkb_logger.info(f'Successfully downloaded and saved file from URL: {url}, file_id: {file_id}')

                return new_file

            except Exception as e:
                maxkb_logger.error(f'Failed to download document file from URL: {url}, error: {str(e)}', exc_info=True)
                raise Exception(f'Failed to download document file: {str(e)}')

        content = []
        document_list = []
        # 批量查询文档文件，避免循环内逐个查询（N+1）
        doc_file_id_list = [doc['file_id'] for doc in document
                            if not isinstance(doc, str) and doc.get('file_id')]
        doc_file_ids = [file_id for file_id in {normalize_uuid(file_id) for file_id in doc_file_id_list} if file_id]
        doc_file_map = {}
        if doc_file_ids:
            doc_file_map = {str(f.id): f for f in QuerySet(File).filter(id__in=doc_file_ids)}
        for doc in document:
            # 考虑API调用时，用户传错了格式，抛出异常提示
            if isinstance(doc, str):
                raise ValueError('The "document_list" parameters must be in the format of `[{ "url": "http......" }, ......]`')

            # 如果是文档的 HTTP(s) URL地址，则先下载并保存到file表中
            if not doc.get("file_id") and doc.get("url") and (doc.get("url").startswith("http:") or doc.get("url").startswith("https:")):
                try:
                    # 下载并保存文件
                    file = download_and_save_file(doc["url"], doc.get('name', None))

                    # 更新doc字典，添加file_id
                    doc['file_id'] = str(file.id)
                    if not doc.get('name'):
                        doc['name'] = file.file_name

                    maxkb_logger.info(f'Downloaded file from URL and assigned file_id: {doc["file_id"]}')
                except Exception as e:
                    maxkb_logger.error(f'Error processing document URL: {doc.get("url")}, error: {str(e)}')
                    raise e
            elif doc.get("file_id"):
                file = doc_file_map.get(normalize_uuid(doc['file_id']))
                if file is None:
                    raise ValueError(f"File not found for file_id: {doc['file_id']}")
            else:
                raise ValueError('Please provide a valid document file ID or URL')

            buffer = io.BytesIO(file.get_bytes())
            buffer.name = doc['name']  # this is the important line

            for split_handle in (parse_table_handle_list + split_handles):
                if split_handle.support(buffer, get_buffer):
                    # 回到文件头
                    buffer.seek(0)
                    file_content = split_handle.get_content(buffer, save_image)
                    content.append('### ' + doc['name'] + '\n' + file_content)
                    document_list.append({'id': str(file.id), 'name': doc['name'], 'content': file_content})
                    break

        return NodeResult({
            'content': splitter.join(content),
            "image_list": extracted_image_list,
            'document_list': document_list
        }, {})

    def get_details(self, index: int, **kwargs):
        content = self.context.get('content', '').split(splitter)
        # 不保存content全部内容，因为content内容可能会很大
        return {
            'name': self.node.properties.get('stepName'),
            "index": index,
            'run_time': self.context.get('run_time'),
            'type': self.node.type,
            'content': [file_content[:500] for file_content in content],
            'status': self.status,
            'err_message': self.err_message,
            'document_list': self.context.get('document_list'),
            'enableException': self.node.properties.get('enableException'),
        }
