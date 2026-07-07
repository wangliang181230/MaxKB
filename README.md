## 当前分支说明

基于官方仓库的 `v2.10.3-lts`（commit id: [fd6141e](https://github.com/1Panel-dev/MaxKB/commit/fd6141e662582e88a41edbb7f6f89f4539e3e5dd)） 分支进行改造的，总共提交了 38 个 Commit，包括：
- 11 个 feat
- 02 个 fix
- 25 个 perf

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
            crpi-eomrzdj73f5p8zyb.cn-hangzhou.personal.cr.aliyuncs.com/wangliang181230/maxkb:v2.10.3
        ```

    2. 命令参数说明：

       - 镜像: `crpi-eomrzdj73f5p8zyb.cn-hangzhou.personal.cr.aliyuncs.com/wangliang181230/maxkb:v2.10.3`

           此镜像是基于当前分支（`v2.10.3`）打包的，并不是MaxKB的官方镜像，

       - -p
           - `8080`: MaxKB 的端口
           - `5432`: 内置 PostgreSQL 的端口
           - `6379`: 内置 Redis 的端口

       - -v
           - `~/.maxkb`: 你本地的 MaxKB 数据目录

       - -e （当你需要使用nginx代理出去时，请配置以下两项。）
           - `MAXKB_ADMIN_PATH`: MaxKB 管理界面的路径。
           - `MAXKB_CHAT_PATH`: MaxKB 聊天接口的路径

2. 访问 MaxKB 管理界面 `http://localhost:8080` 使用默认管理员凭据：

    - 用户名: `admin`
    - 密码: `MaxKB@123..`
