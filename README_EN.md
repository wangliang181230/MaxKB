## 当前分支说明

Based on the official repository's `v2.10.3-lts` (commit id: [fd6141e](https://github.com/1Panel-dev/MaxKB/commit/fd6141e662582e88a41edbb7f6f89f4539e3e5dd)) branch for modification, submitted 38 Commits, including:
- 11 features
- 02 fixes
- 25 perf

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
            crpi-eomrzdj73f5p8zyb.cn-hangzhou.personal.cr.aliyuncs.com/wangliang181230/maxkb:v2.10.3
        ```

   2. Parameter Description:

       - Image: `crpi-eomrzdj73f5p8zyb.cn-hangzhou.personal.cr.aliyuncs.com/wangliang181230/maxkb:v2.10.3`

           This image is packaged based on the current branch (`v2.10.3`) and is not an official image from MaxKB.

       - -p
           - `8080`: The port of MaxKB
           - `5432`: The port of PostgreSQL
           - `6379`: The port of Redis

       - -v
           - `~/.maxkb`: Your local MaxKB data directory

       - -e (When you need to use nginx proxy, please configure it.)
           - `MAXKB_ADMIN_PATH`: The path of MaxKB admin interface.
           - `MAXKB_CHAT_PATH`: The path of MaxKB chat interface

2. Access MaxKB web interface at `http://localhost:8080` with default admin credentials:

    - username: `admin`
    - password: `MaxKB@123..`
