# coding=utf-8
"""
    @project: MaxKB
    @Author：wangliang181230
    @file： api_key.py
    @date：2026/9/20 12:09
    @desc: 系统(个人) API Key
"""
import uuid_utils.compat as uuid
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone

from common.mixins.app_model_mixin import AppModelMixin


class SystemApiKey(AppModelMixin):
    id = models.UUIDField(primary_key=True, max_length=128, default=uuid.uuid7, editable=False, verbose_name="主键id")
    secret_key = models.CharField(max_length=1024, verbose_name="秘钥", unique=True)
    user_id = models.CharField(max_length=128, verbose_name="用户id", db_index=True)
    is_active = models.BooleanField(default=True, verbose_name="是否开启")
    allow_cross_domain = models.BooleanField(default=False, verbose_name="是否允许跨域")
    cross_domain_list = ArrayField(verbose_name="跨域列表",
                                   base_field=models.CharField(max_length=128, blank=True),
                                   default=list)
    expire_time = models.DateTimeField(verbose_name="过期时间", default=timezone.now)
    is_permanent = models.BooleanField(default=True, verbose_name="是否永久")

    class Meta:
        db_table = "system_api_key"
