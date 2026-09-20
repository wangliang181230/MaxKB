# Generated migration for SystemApiKey
import uuid_utils.compat
import django.contrib.postgres.fields
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ('system_manage', '0006_chatuser_uid'),
    ]

    operations = [
        migrations.CreateModel(
            name='SystemApiKey',
            fields=[
                ('create_time', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, db_index=True, verbose_name='修改时间')),
                ('id', models.UUIDField(default=uuid_utils.compat.uuid7, editable=False, max_length=128,
                                        primary_key=True, serialize=False, verbose_name='主键id')),
                ('secret_key', models.CharField(max_length=1024, unique=True, verbose_name='秘钥')),
                ('user_id', models.CharField(db_index=True, max_length=128, verbose_name='用户id')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否开启')),
                ('allow_cross_domain', models.BooleanField(default=False, verbose_name='是否允许跨域')),
                ('cross_domain_list',
                 django.contrib.postgres.fields.ArrayField(
                     base_field=models.CharField(blank=True, max_length=128), default=list, size=None,
                     verbose_name='跨域列表')),
                ('expire_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='过期时间')),
                ('is_permanent', models.BooleanField(default=True, verbose_name='是否永久')),
            ],
            options={
                'db_table': 'system_api_key',
                'ordering': ['create_time'],
                'abstract': False,
            },
        ),
    ]
