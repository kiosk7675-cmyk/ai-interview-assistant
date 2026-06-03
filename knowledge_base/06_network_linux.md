# 网络协议与 Linux

## TCP 三次握手？
1. **客户端 → SYN**：客户端发送 SYN=1, seq=x，进入 SYN_SENT 状态。
2. **服务端 → SYN+ACK**：服务端回复 SYN=1, ACK=1, seq=y, ack=x+1，进入 SYN_RCVD 状态。
3. **客户端 → ACK**：客户端发送 ACK=1, seq=x+1, ack=y+1，进入 ESTABLISHED 状态。
- **为什么三次**：防止历史连接（失效 SYN）触发服务端资源分配；确保双方都能确认收发能力。

## TCP 四次挥手？
1. **主动方 → FIN**：请求关闭，进入 FIN_WAIT_1。
2. **被动方 → ACK**：确认收到，进入 CLOSE_WAIT。主动方进入 FIN_WAIT_2。
3. **被动方 → FIN**：被动方也关闭，进入 LAST_ACK。
4. **主动方 → ACK**：确认，进入 TIME_WAIT（等待 2MSL 后关闭）。
- **TIME_WAIT**：确保最后一个 ACK 能到达被动方；让网络中残留的延迟报文消失。持续 2MSL（约 60 秒）。
- **大量 TIME_WAIT**：高频短连接导致，解决：连接池复用、`tcp_tw_reuse=1`（客户端）、增加端口范围。

## HTTP/1.1 vs HTTP/2 vs HTTP/3？
- **HTTP/1.1**：文本协议，队头阻塞（一个 TCP 连接同一时间只处理一个请求），管道化支持差。
- **HTTP/2**：二进制帧、多路复用（一个连接并行多个流）、头部压缩（HPACK）、服务器推送。仍存在 TCP 层队头阻塞。
- **HTTP/3**：基于 QUIC（UDP），0-RTT 连接建立，无 TCP 队头阻塞，连接迁移（IP 变化不断连）。

## HTTPS 原理？
1. **非对称加密**：客户端用服务器公钥加密随机密钥，服务器用私钥解密。
2. **对称加密**：双方用协商的密钥加密通信数据（性能好）。
3. **数字证书**：CA 签发，验证服务器身份，防止中间人攻击。
4. **TLS 1.3**：简化握手（1-RTT 甚至 0-RTT），移除不安全的加密套件。

## Cookie vs Session vs Token？
- **Cookie**：浏览器自动携带，有 CSRF 风险。4KB 限制。HttpOnly 防 XSS 读取，SameSite 防 CSRF。
- **Session**：服务端存储会话数据，Session ID 通过 Cookie 传递。服务端需存储，集群需共享（Redis）。
- **Token（JWT）**：无状态，客户端存储，请求头 Authorization 携带。不依赖服务端存储，但无法主动失效（需黑名单）。
- **刷新 Token**：Access Token 短期（15min），Refresh Token 长期（7d），平衡安全与体验。

## Linux 常用命令？
- **进程**：`ps aux`、`top`/`htop`、`kill -9 PID`、`netstat -tlnp`（查端口）。
- **文件**：`tail -f log.txt`（实时日志）、`grep -rn "error" /var/log/`、`find / -name "*.conf"`。
- **磁盘**：`df -h`（磁盘使用）、`du -sh *`（目录大小）。
- **权限**：`chmod 755 file`、`chown user:group file`。
- **网络**：`curl -v URL`、`ss -tlnp`、`nslookup domain`、`tcpdump -i eth0 port 80`。

## Linux 进程与线程？
- **进程**：资源分配的基本单位，有独立地址空间。
- **线程**：CPU 调度的基本单位，共享进程地址空间。
- **守护进程**：后台运行，脱离终端，如 Nginx worker 进程。
- **信号**：`kill -SIGTERM PID`（优雅退出）、`SIGHUP`（重载配置）。
- **nohup**：`nohup cmd &` 让进程不随终端关闭而退出。

## Docker 基础？
- **镜像**：只读模板，分层存储。`docker build -t app:1.0 .`
- **容器**：镜像的运行实例，可读写层。`docker run -d -p 8080:80 app:1.0`
- **Dockerfile**：`FROM python:3.11` → `WORKDIR /app` → `COPY . .` → `RUN pip install -r requirements.txt` → `CMD ["uvicorn", "main:app", "--host", "0.0.0.0"]`
- **Docker Compose**：多容器编排，`docker-compose up -d` 一键启动。
- **数据卷**：`-v /host/path:/container/path` 持久化数据。
