# coding=utf-8
"""
    @project: maxkb
    @Author：虎
    @file： tokenizer_manage_config.py
    @date：2024/4/28 10:17
    @desc:
"""

import os
import logging

logger = logging.getLogger(__name__)


class MKTokenizer:
    def __init__(self, tokenizer):
        self.tokenizer = tokenizer

    def encode(self, text):
        return self.tokenizer.encode(text).ids


class MKSimpleTokenizer:
    """基于 UTF-8 字节的简单回退 tokenizer，当 bert-base-cased 模型不可用时使用（token 数仅为粗略估计）"""

    def encode(self, text):
        return list(text.encode('utf-8'))


class TokenizerManage:
    tokenizer = None
    # 缓存回退实例，避免模型缺失时在计费热路径上重复构造并刷屏
    _fallback = None

    @staticmethod
    def get_tokenizer():
        # 已成功加载则直接复用，避免计费热路径每次重新解析 tokenizer.json
        if TokenizerManage.tokenizer is not None:
            return MKTokenizer(TokenizerManage.tokenizer)
        from tokenizers import Tokenizer
        # 优先使用项目目录下的模型路径（兼容 Windows 本地开发），回退到 Docker 部署路径
        from maxkb.const import PROJECT_DIR
        candidate_paths = [
            os.path.join(PROJECT_DIR, "model", "tokenizer", "models--bert-base-cased"),
            os.path.join("/opt/maxkb-app", "model", "tokenizer", "models--bert-base-cased"),
        ]
        # 以 refs/main 文件存在为准，避免目录存在但不完整时误判
        model_path = next(
            (p for p in candidate_paths if os.path.isfile(os.path.join(p, "refs", "main"))), None
        )
        if model_path is None:
            if TokenizerManage._fallback is None:
                logger.warning(
                    f"bert-base-cased tokenizer model not found in {candidate_paths}, "
                    f"falling back to approximate byte-level tokenizer (token counts are only estimated)"
                )
                TokenizerManage._fallback = MKSimpleTokenizer()
            return TokenizerManage._fallback
        refs_file = os.path.join(model_path, "refs", "main")
        with open(refs_file, encoding="utf-8") as f:
            snapshot = f.read()
        TokenizerManage.tokenizer = Tokenizer.from_file(
            os.path.join(model_path, "snapshots", snapshot, "tokenizer.json")
        )
        return MKTokenizer(TokenizerManage.tokenizer)
