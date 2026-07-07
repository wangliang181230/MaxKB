## 当前分支说明

基于官方仓库的 `v2.10.6-lts`（commit: [0bb81c71](https://github.com/1Panel-dev/MaxKB/commits/0bb81c71)） 分支进行改造的，总共提交了 57 个 Commit，包括：
- 15 个 feat
- 33 个 perf
- 09 个 fix

[详情请看变更记录](https://github.com/wangliang181230/MaxKB/compare/0bb81c71...49e3366d)

## 快速启动

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
            crpi-eomrzdj73f5p8zyb.cn-hangzhou.personal.cr.aliyuncs.com/wangliang181230/maxkb:v2.10.6
        ```

    2. 命令参数说明：

       - 镜像: `crpi-eomrzdj73f5p8zyb.cn-hangzhou.personal.cr.aliyuncs.com/wangliang181230/maxkb:v2.10.6`

           此镜像是基于当前分支（`v2.10.6`）打包的，并不是MaxKB的官方镜像，

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
