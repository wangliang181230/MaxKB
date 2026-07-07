## 当前分支说明

基于官方仓库的 `v2.10.8-lts`（commit: [c09b873b](https://github.com/1Panel-dev/MaxKB/commits/c09b873b)） 分支进行改造的，总共提交了 56 个 Commit，包括：
- 15 个 feat
- 34 个 perf
- 07 个 fix

[详情请看变更记录](https://github.com/wangliang181230/MaxKB/compare/c09b873b...c5756f15)

## 快速启动~~~~

1. 执行以下脚本，使用Docker启动MaxKB容器：
    1. Docker命令：
        ```bash
        docker run \
            -d \
            --name=maxkb \
            --restart=always \
            -p 8080:8080 \
            -p 5432:5432 \
            -p 6379:6379 \
            -v ~/.maxkb:/opt/maxkb \
            -e MAXKB_ADMIN_PATH=/maxkb/admin \
            -e MAXKB_CHAT_PATH=/maxkb/chat \
            crpi-eomrzdj73f5p8zyb.cn-hangzhou.personal.cr.aliyuncs.com/wangliang181230/maxkb:v2.10.8
        ```

    2. 命令参数说明：

       - 镜像: `crpi-eomrzdj73f5p8zyb.cn-hangzhou.personal.cr.aliyuncs.com/wangliang181230/maxkb:v2.10.8`

           此镜像是基于当前分支（`v2.10.8`）打包的，并不是MaxKB的官方镜像，

       - -p
           - `8080`: MaxKB 的端口
           - `5432`: 内置 PostgreSQL 的端口，默认用户名：`root`，默认密码：`Password123@postgres`
           - `6379`: 内置 Redis 的端口，默认密码：`Password123@redis`

       - -v
           - `~/.maxkb`: 你本地的 MaxKB 数据目录

       - -e （当你需要使用nginx代理出去时，请配置以下两项。）
           - `MAXKB_ADMIN_PATH`: MaxKB `管理`页面的根路径，不配置时，默认值为 `/admin`
           - `MAXKB_CHAT_PATH`: MaxKB `聊天`页面的根路径，不配置时，默认值为 `/chat`

2. 访问 MaxKB 管理界面 `http://localhost:8080` 使用默认管理员凭据：

    - 用户名: `admin`
    - 密码: `MaxKB@123..`

3. 如有问题，请发邮件给我，我会免费帮助大家解决问题： [841369634@qq.com](mailto:841369634@qq.com)
