## 当前分支说明

Based on the official repository's `v2.10.5-lts` (commit: [01b21db](https://github.com/1Panel-dev/MaxKB/commits/01b21db)) branch for modification, submitted 52 commits, including:
- 14 features
- 31 perf
- 07 fixes

[See the change record for details](https://github.com/wangliang181230/MaxKB/compare/01b21db...5851b112)

## Quick start

1. Execute the script below to start a MaxKB container using Docker:
    1.  Docker command：
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
            crpi-eomrzdj73f5p8zyb.cn-hangzhou.personal.cr.aliyuncs.com/wangliang181230/maxkb:v2.10.5
        ```

   2. Parameter Description:

       - Image: `crpi-eomrzdj73f5p8zyb.cn-hangzhou.personal.cr.aliyuncs.com/wangliang181230/maxkb:v2.10.5`

           This image is packaged based on the current branch (`v2.10.5`) and is not an official image from MaxKB.

       - -p
           - `8080`: The port of MaxKB
           - `5432`: The port of PostgreSQL. Default user: `root`, default password: `Password123@postgres`
           - `6379`: The port of Redis. Default password: `Password123@redis`

       - -v
           - `~/.maxkb`: Your local MaxKB data directory

       - -e (When you need to use nginx proxy, please configure it.)
           - `MAXKB_ADMIN_PATH`: The root path of the admin page. Default is `/admin`
           - `MAXKB_CHAT_PATH`: The root path of the chat page. Default is `/chat`

2. Access MaxKB web interface at `http://localhost:8080` with default admin credentials:

    - username: `admin`
    - password: `MaxKB@123..`

3. If you have any questions, please email me, and I will help you solve them: [841369634@qq.com](mailto:841369634@qq.com)
