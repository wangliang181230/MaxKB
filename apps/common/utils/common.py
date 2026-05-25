# coding=utf-8
"""
    @project: MaxKB
    @Author：虎虎
    @file： common.py
    @date：2025/4/14 18:23
    @desc:
"""
import datetime
import hashlib
import io
import json
import mimetypes
import pickle
import random
import re
import shutil
import uuid
from functools import reduce
from typing import List, Dict
import pytz
from django.contrib.auth.hashers import check_password, make_password
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db.models import QuerySet
from django.utils.translation import gettext as _
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
from pydub import AudioSegment
from urllib.parse import urlparse

from maxkb.settings import TIME_ZONE
from ..database_model_manage.database_model_manage import DatabaseModelManage
from ..exception.app_exception import AppApiException


def _legacy_md5_hash(row_password):
    """
    Legacy MD5 hashing — used only to detect old hashes during migration.
    Do NOT use for new passwords.
    """
    md5 = hashlib.md5()
    md5.update(row_password.encode())
    return md5.hexdigest()


def password_encrypt(row_password):
    """
    密码加密（使用 Django PBKDF2）
    :param row_password: 密码
    :return:  加密后密码
    """
    return make_password(row_password)


def password_verify(row_password, hashed_password):
    """
    验证密码是否匹配已存储的哈希值。
    支持透明升级：如果存储的是旧版 MD5 哈希，也能正确验证。
    :param row_password: 明文密码
    :param hashed_password: 数据库中存储的密码哈希
    :return: 是否匹配
    """
    # First try Django's built-in check (PBKDF2, bcrypt, argon2, etc.)
    if check_password(row_password, hashed_password):
        return True
    # Fall back to legacy MD5 comparison for not-yet-migrated hashes
    if _is_legacy_md5_hash(hashed_password):
        return _legacy_md5_hash(row_password) == hashed_password
    return False


def _is_legacy_md5_hash(hashed_password):
    """
    Detect legacy unsalted MD5 hex-digest hashes (exactly 32 hex chars).
    Django password hashes always contain '$' separators.
    """
    if hashed_password and len(hashed_password) == 32:
        try:
            int(hashed_password, 16)
            return True
        except ValueError:
            pass
    return False


def needs_password_upgrade(hashed_password):
    """
    Check if a stored password hash should be upgraded to PBKDF2.
    Returns True for legacy MD5 hashes.
    """
    return _is_legacy_md5_hash(hashed_password)


def group_by(list_source: List, key):
    """
    將數組分組
    :param list_source: 需要分組的數組
    :param key: 分組函數
    :return: key->[]
    """
    result = {}
    for e in list_source:
        k = key(e)
        array = result.get(k) if k in result else []
        array.append(e)
        result[k] = array
    return result


SAFE_CHAR_SET = (
        [chr(i) for i in range(65, 91) if chr(i) not in {'I', 'O'}] +  # 大写字母 A-H, J-N, P-Z
        [chr(i) for i in range(97, 123) if chr(i) not in {'i', 'l', 'o'}] +  # 小写字母 a-h, j-n, p-z
        [str(i) for i in range(10) if str(i) not in {'0', '1', '7'}]  # 数字 2-6, 8-9
)


def get_random_chars(number=4):
    if number <= 0:
        return ""
    return ''.join(random.choices(SAFE_CHAR_SET, k=number))


def encryption(message: str):
    """
        加密敏感字段数据  加密方式是 如果密码是 1234567890  那么给前端则是 123******890
    :param message:
    :return:
    """
    if not message:  # 处理空字符串情况
        return "***************"
    max_pre_len = 8
    max_post_len = 4
    message_len = len(message)
    pre_len = int(message_len / 5 * 2)
    post_len = int(message_len / 5 * 1)
    pre_str = "".join([message[index] for index in
                       range(0, max_pre_len if pre_len > max_pre_len else 1 if pre_len <= 0 else int(pre_len))])
    end_str = "".join(
        [message[index] for index in
         range(message_len - (post_len if post_len < max_post_len else max_post_len), message_len)])
    content = "***************"
    return pre_str + content + end_str


def _remove_empty_lines(text):
    if not isinstance(text, str):
        raise AppApiException(500, _('Text-to-speech node, the text content must be of string type'))
    if not text:
        raise AppApiException(500, _('Text-to-speech node, the text content cannot be empty'))
    result = '\n'.join(line for line in text.split('\n') if line.strip())
    return markdown_to_plain_text(result)


def markdown_to_plain_text(md: str) -> str:
    # 移除图片 ![alt](url)
    text = re.sub(r'!\[.*?\]\(.*?\)', '', md)
    # 移除链接 [text](url)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    # 移除 Markdown 标题符号 (#, ##, ###)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    # 移除加粗 **text** 或 __text__
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'__(.*?)__', r'\1', text)
    # 移除斜体 *text* 或 _text_
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'_(.*?)_', r'\1', text)
    # 移除行内代码 `code`
    text = re.sub(r'`(.*?)`', r'\1', text)
    # 移除代码块 ```code```
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    # 移除多余的换行符
    text = re.sub(r'\n{2,}', '\n', text)
    # 使用正则表达式去除所有 HTML 标签
    text = re.sub(r'<[^>]+>', '', text)
    # 先移除特定媒体标签（优先级高于通用HTML标签移除）
    text = re.sub(r'<(?:audio|video)(?:\s+[^>]*)?>.*?(?:</(?:audio|video)>)?', '', text,
                  flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<img[^>]*>', '', text)  # 匹配图片标签
    # 去除多余的空白字符（包括换行符、制表符等）
    text = re.sub(r'\s+', ' ', text)
    # 去除表单渲染
    text = re.sub(r'<form_rander>.*?<\/form_rander>', '', text, flags=re.DOTALL)
    # 去除首尾空格
    text = text.strip()
    return text


def get_file_content(path):
    with open(path, "r", encoding='utf-8') as file:
        content = file.read()
    return content


def sub_array(array: List, item_num=10):
    result = []
    temp = []
    for item in array:
        temp.append(item)
        if len(temp) >= item_num:
            result.append(temp)
            temp = []
    if len(temp) > 0:
        result.append(temp)
    return result


def bytes_to_uploaded_file(file_bytes, file_name="file.txt"):
    content_type, _ = mimetypes.guess_type(file_name)
    if content_type is None:
        # 如果未能识别，设置为默认的二进制文件类型
        content_type = "application/octet-stream"
    # 创建一个内存中的字节流对象
    file_stream = io.BytesIO(file_bytes)

    # 获取文件大小
    file_size = len(file_bytes)

    # 创建 InMemoryUploadedFile 对象
    uploaded_file = InMemoryUploadedFile(
        file=file_stream,
        field_name=None,
        name=file_name,
        content_type=content_type,
        size=file_size,
        charset=None,
    )
    return uploaded_file


def any_to_amr(any_path, amr_path):
    """
    把任意格式转成amr文件
    """
    if any_path.endswith(".amr"):
        shutil.copy2(any_path, amr_path)
        return
    if any_path.endswith(".sil") or any_path.endswith(".silk") or any_path.endswith(".slk"):
        raise NotImplementedError("Not support file type: {}".format(any_path))
    audio = AudioSegment.from_file(any_path)
    audio = audio.set_frame_rate(8000)  # only support 8000
    audio.export(amr_path, format="amr")
    return audio.duration_seconds * 1000


def any_to_mp3(any_path, mp3_path):
    """
    把任意格式转成mp3文件
    """
    if any_path.endswith(".mp3"):
        shutil.copy2(any_path, mp3_path)
        return
    if any_path.endswith(".sil") or any_path.endswith(".silk") or any_path.endswith(".slk"):
        sil_to_wav(any_path, any_path)
        any_path = mp3_path
    audio = AudioSegment.from_file(any_path)
    audio = audio.set_frame_rate(16000)
    audio.export(mp3_path, format="mp3")


def sil_to_wav(silk_path, wav_path, rate: int = 24000):
    """
    silk 文件转 wav
    """
    try:
        import pysilk
    except ImportError:
        raise AppApiException("import pysilk failed, wechaty voice message will not be supported.")
    wav_data = pysilk.decode_file(silk_path, to_wav=True, sample_rate=rate)
    with open(wav_path, "wb") as f:
        f.write(wav_data)


def split_and_transcribe(file_path, model, max_segment_length_ms=59000, audio_format="mp3"):
    audio_data = AudioSegment.from_file(file_path, format=audio_format)
    audio_length_ms = len(audio_data)

    if audio_length_ms <= max_segment_length_ms:
        return model.speech_to_text(io.BytesIO(audio_data.export(format=audio_format).read()))

    full_text = []
    for start_ms in range(0, audio_length_ms, max_segment_length_ms):
        end_ms = min(audio_length_ms, start_ms + max_segment_length_ms)
        segment = audio_data[start_ms:end_ms]
        text = model.speech_to_text(io.BytesIO(segment.export(format=audio_format).read()))
        if isinstance(text, str):
            full_text.append(text)
    return ' '.join(full_text)


def query_params_to_single_dict(query_params: Dict):
    return reduce(lambda x, y: {**x, **y}, list(
        filter(lambda item: item is not None, [({key: value} if value is not None and len(value) > 0 else None) for
                                               key, value in
                                               query_params.items()])), {})


def valid_license(model=None, count=None, message=None):
    def inner(func):
        def run(*args, **kwargs):
            is_license_valid = DatabaseModelManage.get_model('license_is_valid')
            is_license_valid = is_license_valid() if is_license_valid() is not None else False
            record_count = QuerySet(model).count()

            if not is_license_valid and record_count >= count:
                error_message = message or _(
                    'Limit {count} exceeded, please contact us (https://fit2cloud.com/).').format(
                    count=count)
                raise AppApiException(400, error_message)

            return func(*args, **kwargs)

        return run

    return inner


def post(post_function):
    def inner(func):
        def run(*args, **kwargs):
            result = func(*args, **kwargs)
            return post_function(*result)

        return run

    return inner


def parse_md_image(content: str):
    matches = re.finditer("!\[.*?\]\(.*?\)", content)
    image_list = [match.group() for match in matches]
    return image_list


def bulk_create_in_batches(model, data, batch_size=1000):
    if len(data) == 0:
        return
    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        model.objects.bulk_create(batch)


def get_sha256_hash(_v: str | bytes):
    sha256 = hashlib.sha256()
    if isinstance(_v, str):
        sha256.update(_v.encode())
    else:
        sha256.update(_v)
    return sha256.hexdigest()


ALLOWED_CLASSES = {
    ("builtins", "dict"),
    ('uuid', 'UUID'),
    ("application.serializers.application", "MKInstance"),
    ("tools.serializers.tool", "ToolInstance"),
    ("knowledge.serializers.knowledge_workflow", "KBWFInstance")
}


class RestrictedUnpickler(pickle.Unpickler):

    def find_class(self, module, name):
        if (module, name) in ALLOWED_CLASSES:
            return super().find_class(module, name)
        raise pickle.UnpicklingError("global '%s.%s' is forbidden" %
                                     (module, name))


def restricted_loads(s):
    """Helper function analogous to pickle.loads()."""
    return RestrictedUnpickler(io.BytesIO(s)).load()


def flat_map(array: List[List]):
    """
    将二位数组转为一维数组
    :param array: 二维数组
    :return: 一维数组
    """
    result = []
    for e in array:
        result += e
    return result


def parse_image(content: str):
    matches = re.finditer("!\[.*?\]\(\.\/oss\/(image|file)\/.*?\)", content)
    image_list = [match.group() for match in matches]
    return image_list


def generate_uuid(tag: str):
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, tag))


def filter_workspace(query_list):
    return [q for q in query_list if q.name != "workspace_id"]


def filter_special_character(_str):
    """
    过滤特殊字符
    """
    s_list = ["\\u0000"]
    for t in s_list:
        _str = _str.replace(t, '')
    return _str


def is_valid_uuid(uuid_string):
    """判断字符串是否为有效的UUID"""
    try:
        uuid_obj = uuid.UUID(uuid_string)
        return str(uuid_obj) == uuid_string
    except ValueError:
        return False


def common_convert_value(_type, value):
    if value is None:
        return None

    if _type == 'int':
        return int(value)
    if _type == 'boolean':
        if isinstance(value, str) and value.lower() in ('false', '0', '[]', ''):
            return False
        return bool(value)
    if _type == 'float':
        return float(value)
    if _type == 'dict':
        if isinstance(value, dict):
            return value
        v = json.loads(value)
        if isinstance(v, dict):
            return v
        raise Exception(_('type error'))
    if _type == 'array':
        if isinstance(value, list):
            return value
        v = json.loads(value)
        if isinstance(v, list):
            return v
        raise Exception(_('type error'))
    return value


def reset_value(value):
    if isinstance(value, str):
        value = re.sub(ILLEGAL_CHARACTERS_RE, '', value)
        if value.startswith(('=', '+', '-', '@')):
            value = "'" + value
    if isinstance(value, datetime.datetime):
        eastern = pytz.timezone(TIME_ZONE)
        c = datetime.timezone(eastern._utcoffset)
        value = value.astimezone(c)
    return value


def get_file_name_from_content_disposition(content_disposition: str, default: str = None) -> str:
    """
    尝试从响应头 `Content-Disposition` 中获取文件名

    :param content_disposition: 响应头 `Content-Disposition`
    :param default:             默认文件名
    :return: 文件名
    """
    if not content_disposition:
        return default

    file_name = default
    if 'filename=' in content_disposition:
        filename_part = content_disposition.split('filename=')[1].split(';')[0].strip('"\'')
        if filename_part:
            file_name = filename_part

    return file_name


def get_file_name_from_url(url: str, default: str = None) -> str:
    """
    尝试从url中获取文件名
    :param url:     文件URL地址
    :param default: 默认文件名
    :return: 文件名
    """
    if not url:
        return default

    parsed_url = urlparse(url)
    path_parts = parsed_url.path.split('/')
    return path_parts[-1] if path_parts and path_parts[-1] else default


def _check_office_type(file_bytes: bytes) -> str:
    """区分 zip 压缩包内的 office 类型"""
    content = file_bytes.decode("ISO-8859-1", errors="ignore")
    if "word/" in content:
        return "docx"
    elif "xl/" in content:
        return "xlsx"
    elif "ppt/" in content:
        return "pptx"
    return "zip"

def get_file_type_from_bytes(file_bytes: bytes):
    """
    从文件二进制 bytes 判断文件类型
    :param file_bytes: 文件二进制
    :return: 文件后缀（如 pdf、png、jpg、zip、xlsx 等）
    """
    # 如果没有16个字节，则无法判断
    if len(file_bytes) < 16:
        return None

    # 读取前16个字节（足够判断绝大多数文件）
    header = file_bytes[:16].hex().lower()

    # 常见文件签名对照表
    signatures = {
        # 图片
        "ffd8ffe0": "jpg",
        "ffd8ffdb": "jpg",
        "89504e47": "png",
        "47494638": "gif",

        # 文档
        "25504446": "pdf",
        "d0cf11e0": "doc",  # office 97-2003
        "504b0304": "zip",  # 新office/zip通用

        # 压缩包
        "52617221": "rar",
        "377abcaf": "7z",
        "425a68": "bz2",
        "1f8b": "gz",

        # 视频音频
        "494433": "mp3",
        "00000018": "mp4",
        "1a45dfa3": "mkv",
    }

    # 先匹配普通唯一签名
    for sig, ext in signatures.items():
        if header.startswith(sig):
            if ext == "zip":
                return _check_office_type(file_bytes)
            return ext

    # RIFF 开头的格式：WebP / WAV / AVI
    if header.startswith("52494646"):
        # 第 8-12 字节区分类型
        sub_type = file_bytes[8:12].hex().lower()
        if sub_type == "57454250":  # WEBP
            return "webp"
        elif sub_type == "57415645":  # WAVE
            return "wav"
        elif sub_type == "41564920":  # AVI
            return "avi"

    return None


def get_file_type_from_content_type(content_type: str):
    """
    从 HTTP 响应头 Content-Type 解析出文件后缀
    :param content_type: 响应头里的 Content-Type，例如 "image/png"、"application/pdf"
    :return: 文件后缀（不带点），如 png、pdf、jpg，无法识别返回 None
    """
    if not content_type:
        return None

    # 统一转小写，去掉编码等无关参数（例如 text/html; charset=utf-8）
    content_type = content_type.lower().split(';')[0].split('/')[-1].strip()
    if not content_type:
        return None

    # 需要转换的 Content-Type 后缀映射表
    mime_map = {
        # 图片
        "svg+xml": "svg",

        # 文档
        "msword": "doc",
        "ms-word": "doc",
        "vnd.ms-word": "doc",
        "vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
        "vnd.ms-excel": "xls",
        "vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
        "vnd.ms-powerpoint": "ppt",
        "vnd.openxmlformats-officedocument.presentationml.presentation": "pptx",
        "plain": "txt",

        # 压缩包
        "x-rar-compressed": "rar",
        "x-7z-compressed": "7z",
        "gzip": "gz",
        "x-bzip2": "bz2",

        # 音视频
        "mpeg": "mp3",
        "x-matroska": "mkv",
    }

    # 获取文件后缀名
    file_type = mime_map.get(content_type) or content_type

    # 如果长度小于等于32，则视为正常的文件类型
    return file_type if len(file_type) <= 32 else None


def get_file_name_from_url_or_response(url, response, default=None):
    def is_known_type_file_name(name) -> bool:
        # 判断是否有后缀名的文件名
        return True if name and "." in name and not name.endswith(".") else False

    # 1. 先从 `响应头 Content-Disposition` 中获取文件名
    file_name1 = get_file_name_from_content_disposition(response.headers.get('Content-Disposition'))
    if is_known_type_file_name(file_name1):
        return file_name1

    # 2. 再从URL路径中提取文件名
    file_name2 = get_file_name_from_url(url)
    if is_known_type_file_name(file_name2):
        return file_name2

    file_name = file_name1 or file_name2 or default
    if not file_name:
        file_name = "downloaded_file"
    elif is_known_type_file_name(file_name):
        return file_name

    # 获取并判断是否成功下载文件
    file_bytes = response.content
    if not isinstance(file_bytes, bytes):
        return file_name

    # 3. 如果没有获取到文件类型，则尝试从 `file_bytes` 或 `响应头 Content-Type` 中获取文件类型
    file_type = get_file_type_from_bytes(file_bytes) or get_file_type_from_content_type(response.headers.get('Content-Type'))
    if file_type:
        file_name += f".{file_type}"

    return file_name
