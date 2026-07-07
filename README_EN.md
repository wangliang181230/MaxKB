## 当前分支说明

Based on the official repository's `v2.10.4-lts` (commit: [69701d4](https://github.com/1Panel-dev/MaxKB/commits/69701d4)) branch for modification, submitted 46 commits, including:
- 12 features
- 28 perf
- 06 fixes

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
            crpi-eomrzdj73f5p8zyb.cn-hangzhou.personal.cr.aliyuncs.com/wangliang181230/maxkb:v2.10.4
        ```

   2. Parameter Description:

       - Image: `crpi-eomrzdj73f5p8zyb.cn-hangzhou.personal.cr.aliyuncs.com/wangliang181230/maxkb:v2.10.4`

           This image is packaged based on the current branch (`v2.10.4`) and is not an official image from MaxKB.

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
