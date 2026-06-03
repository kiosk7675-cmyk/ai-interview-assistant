# DevOps 与云计算面经

## Linux 基础

### 常用命令
- 进程管理：`ps aux`、`top`/`htop`、`kill -9`、`nohup`
- 文件操作：`find / -name "*.log" -mtime +7`、`grep -rn "error" /var/log/`、`awk '{print $1}'`、`sed -i 's/old/new/g'`
- 网络排查：`netstat -tlnp`、`ss -s`、`curl -v`、`tcpdump`、`nslookup`/`dig`
- 磁盘：`df -h`、`du -sh *`、`fdisk`、`mount`
- 权限：`chmod 755`、`chown user:group`、`sudo`

### 文件权限与用户管理
权限格式：rwxrwxrwx（属主/属组/其他）。4=r, 2=w, 1=x。SUID：执行时以文件属主身份运行。SGID：执行时以属组身份运行/新建文件继承目录属组。用户管理：`useradd`、`usermod`、`passwd`、`/etc/sudoers`。

### Shell 脚本
条件：`if [ -f file ]; then ... fi`。循环：`for i in $(seq 1 10); do ... done`。函数、变量、`$?` 退出码、`$0` 脚本名、`$@` 所有参数。定时任务：`crontab -e`（分时日月周）。

## Docker

### Docker 核心概念
镜像（Image）：只读模板，分层存储。容器（Container）：镜像的运行实例，可读写层。仓库（Registry）：镜像存储分发（Docker Hub / 私有仓库）。Dockerfile：构建镜像的指令文件。

### Dockerfile 常用指令
`FROM` 基础镜像、`WORKDIR` 工作目录、`COPY/ADD` 复制文件、`RUN` 构建时执行、`ENV` 环境变量、`EXPOSE` 声明端口、`CMD` 容器启动命令（可被覆盖）、`ENTRYPOINT` 入口点（不可覆盖，配合 CMD 传参）。多阶段构建减小镜像体积。

### Docker Compose
定义多容器应用。`docker-compose.yml` 声明服务、网络、卷。`depends_on` 控制启动顺序。`volumes` 数据持久化。`networks` 服务隔离。常用：`docker-compose up -d`、`docker-compose logs -f`、`docker-compose down -v`。

### Docker 网络
Bridge（默认，容器间通过虚拟网桥通信）、Host（共享宿主网络栈）、None（无网络）、Overlay（跨主机通信，Swarm/K8s 用）。容器间通信：服务名解析（Compose 默认）。

## Kubernetes

### K8s 核心资源
- Pod：最小调度单元，一个或多个容器共享网络和存储
- Deployment：管理无状态应用，滚动更新、回滚
- Service：稳定访问端点，ClusterIP/NodePort/LoadBalancer
- ConfigMap/Secret：配置和敏感信息管理
- Ingress：HTTP 路由规则，域名/路径到 Service 的映射
- PV/PVC：持久化存储抽象

### Pod 生命周期
Pending → Running → Succeeded/Failed。健康检查：livenessProbe（重启容器）、readinessProbe（从 Service 摘除）、startupProbe（启动探针）。Init Container：在主容器前执行初始化任务。

### 调度与伸缩
nodeSelector/nodeAffinity：节点调度约束。taint/toleration：污点与容忍。HPA（水平自动伸缩）：基于 CPU/内存/自定义指标自动扩缩。资源请求与限制：requests（调度依据）、limits（上限，超限 OOMKilled）。

## CI/CD

### Jenkins / GitLab CI
Jenkins：Pipeline as Code（Jenkinsfile），声明式/脚本式流水线。Agent 分配、Shared Libraries。GitLab CI：`.gitlab-ci.yml` 定义流水线，Runner 执行。Stage/Job/Only/Except 规则。

### CI/CD 最佳实践
代码提交 → 自动构建 → 单元测试 → 代码扫描 → 构建镜像 → 推送仓库 → 部署测试环境 → 集成测试 → 人工审批 → 部署生产。蓝绿部署：两套环境切换。金丝雀发布：小流量验证后逐步扩大。滚动更新：逐个替换实例。

## 云服务

### 云计算模型
IaaS（基础设施即服务）：EC2/ECS，租用虚拟机。PaaS（平台即服务）：函数计算/Cloud Run，只管代码。SaaS（软件即服务）：开箱即用。Serverless：按调用计费，自动伸缩，无服务器管理。

### 对象存储
S3/OSS：Bucket + Key 组织对象。ACL/Policy 权限控制。生命周期策略自动归档/删除。CDN 加速分发。Presigned URL 临时授权访问。

### 监控与可观测性
指标（Metrics）：Prometheus + Grafana，时序数据采集与可视化。日志（Logs）：ELK（Elasticsearch + Logstash + Kibana）/ Loki。链路追踪（Traces）：Jaeger / SkyWalking。告警：Alertmanager / 云监控。
