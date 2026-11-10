# coding=utf-8
from enum import Enum

from models_provider.impl.aliyun_bai_lian_model_provider.aliyun_bai_lian_model_provider import \
    AliyunBaiLianModelProvider
from models_provider.impl.deepseek_model_provider.deepseek_model_provider import DeepSeekModelProvider
from models_provider.impl.local_model_provider.local_model_provider import LocalModelProvider
from models_provider.impl.ollama_model_provider.ollama_model_provider import OllamaModelProvider
from models_provider.impl.openai_model_provider.openai_model_provider import OpenAIModelProvider
from models_provider.impl.siliconCloud_model_provider.siliconCloud_model_provider import SiliconCloudModelProvider
from models_provider.impl.tencent_model_provider.tencent_model_provider import TencentModelProvider
from models_provider.impl.vllm_model_provider.vllm_model_provider import VllmModelProvider
from models_provider.impl.volcanic_engine_model_provider.volcanic_engine_model_provider import \
    VolcanicEngineModelProvider
from models_provider.impl.zhipu_model_provider.zhipu_model_provider import ZhiPuModelProvider


class ModelProvideConstants(Enum):
    # model_azure_provider = AzureModelProvider()
    # model_wenxin_provider = WenxinModelProvider()
    model_ollama_provider = OllamaModelProvider()
    model_openai_provider = OpenAIModelProvider()
    # model_docker_ai_provider = DockerModelProvider()
    # model_kimi_provider = KimiModelProvider()
    model_zhipu_provider = ZhiPuModelProvider()
    # model_xf_provider = XunFeiModelProvider()
    model_deepseek_provider = DeepSeekModelProvider()
    # model_gemini_provider = GeminiModelProvider()
    model_volcanic_engine_provider = VolcanicEngineModelProvider()
    model_tencent_provider = TencentModelProvider()
    # model_aws_bedrock_provider = BedrockModelProvider()
    model_local_provider = LocalModelProvider()
    # model_xinference_provider = XinferenceModelProvider()
    model_vllm_provider = VllmModelProvider()
    aliyun_bai_lian_model_provider = AliyunBaiLianModelProvider()
    # model_anthropic_provider = AnthropicModelProvider()
    model_siliconCloud_provider = SiliconCloudModelProvider()
    # model_regolo_provider = RegoloModelProvider()
    # model_minimax_provider = MiniMaxModelProvider()
