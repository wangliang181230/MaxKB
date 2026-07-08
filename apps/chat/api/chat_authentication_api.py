# coding=utf-8
"""
    @project: MaxKB
    @Author：虎虎
    @file： chat_authentication_api.py
    @date：2025/6/6 19:59
    @desc:
"""

from django.utils.translation import gettext_lazy as _
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter

from chat.serializers.chat import OpenAIInstanceSerializer
from chat.serializers.chat_authentication import AnonymousAuthenticationSerializer
from common.mixins.api_mixin import APIMixin


class OpenAIAPI(APIMixin):
    @staticmethod
    def get_request():
        return OpenAIInstanceSerializer


class ChatAuthenticationAPI(APIMixin):
    @staticmethod
    def get_request():
        return AnonymousAuthenticationSerializer

    @staticmethod
    def get_parameters():
        pass

    @staticmethod
    def get_response():
        pass


class ChatAuthenticationProfileAPI(APIMixin):

    @staticmethod
    def get_parameters():
        return [OpenApiParameter(
            name="access_token",
            description=_("access_token"),
            type=OpenApiTypes.STR,
            location='query',
            required=True,
        )]


class ChatOpenAPI(APIMixin):
    @staticmethod
    def get_parameters():
        return [
            OpenApiParameter(
                name="chat_user_id",
                description="对话用户id",
                type=OpenApiTypes.STR,
                location='query',
                required=False,
            ),
            OpenApiParameter(
                name="username",
                description="姓名",
                type=OpenApiTypes.STR,
                location='query',
                required=False,
            ),
            OpenApiParameter(
                name="email",
                description="电子邮箱",
                type=OpenApiTypes.STR,
                location='query',
                required=False,
            ),
            OpenApiParameter(
                name="phone",
                description="手机号",
                type=OpenApiTypes.STR,
                location='query',
                required=False,
            ),
            OpenApiParameter(
                name="group_id",
                description="用户组ID（common_user=公众用户、medical_worker=医务工作者、manager=后台管理员、assistant=助理、escort=陪护工）",
                type=OpenApiTypes.STR,
                location='query',
                required=False,
            ),
        ]
