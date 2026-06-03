# Go 后端开发面经

## Go 语言基础

### Goroutine 与调度器
Goroutine 是用户态轻量线程，初始栈 2KB（可动态扩缩）。GMP 调度模型：G（Goroutine）→ M（Machine/线程）→ P（Processor/逻辑处理器）。P 的本地队列存放 G，M 绑定 P 执行 G。工作窃取：P 空闲时从其他 P 偷 G 执行。系统调用时 M 释放 P，避免阻塞其他 G。

### Channel 与并发模式
Channel 是 Goroutine 间通信的原语，"不要通过共享内存来通信，而应通过通信来共享内存"。无缓冲 channel：发送和接收必须同时就绪（同步）。有缓冲 channel：缓冲区满前发送不阻塞。常见模式：Fan-In/Fan-Out、Pipeline、Worker Pool、Context 取消。

### Context 包
`context.Context` 用于传递截止时间、取消信号和请求级值。`context.WithCancel`、`context.WithTimeout`、`context.WithDeadline`。惯例：函数第一个参数为 `ctx context.Context`。`select` + `ctx.Done()` 实现超时/取消。

### Slice 与 Map 底层
Slice：`runtime.slice` 结构包含指针、长度(len)、容量(cap)。append 超出 cap 时扩容（<1024 翻倍，≥1024 按 1.25 倍）。Slice 共享底层数组，修改可能影响原 Slice。
Map：哈希表实现，每个桶 8 个键值对。负载因子 6.5 时扩容（等量扩容/翻倍扩容）。Map 非并发安全，`sync.Map` 用于并发读多写少场景。

### Interface 接口
隐式实现：类型只要实现了接口的所有方法就自动满足该接口（鸭子类型）。空接口 `interface{}` 可接收任意类型。类型断言：`v, ok := i.(T)`。Type Switch：`switch v := i.(type)`。nil interface：值为 nil 但类型不为 nil 时，interface != nil。

### defer 与 panic/recover
defer：LIFO 顺序执行，常用于资源释放。defer 时参数已求值。panic 触发后依次执行当前 Goroutine 的 defer，recover 在 defer 中调用可捕获 panic。跨 Goroutine 的 panic 无法 recover。

## Web 框架

### Gin 框架
基于 httprouter 的高性能框架。路由：参数路由 `:id`、通配符 `*path`。中间件：`c.Next()` 调用后续处理函数。Context：请求参数获取、JSON 绑定/渲染。分组路由：`r.Group("/api/v1")`。

### Go 标准库 HTTP 服务
`http.Handler` 接口：`ServeHTTP(ResponseWriter, *Request)`。`http.ServeMux` 路由匹配。`http.ListenAndServe` 启动服务。优雅关闭：`http.Server.Shutdown(ctx)` 配合信号监听。

## 数据库与中间件

### GORM
Go 最流行的 ORM。模型定义用 struct tag（`gorm:"column:name"`）。CRUD：`Create/Find/Save/Delete`。预加载：`Preload("Orders")`。事务：`db.Transaction(func(tx *gorm.DB) error {...})`。原生 SQL：`db.Raw()/db.Exec()`。

### Go 操作 Redis
`go-redis` 客户端。Pipeline 批量执行减少 RTT。Lua 脚本保证原子性。分布式锁：Redlock 算法或 `SET key value NX EX`。

### gRPC 与 Protobuf
gRPC：基于 HTTP/2 + Protobuf 的高性能 RPC 框架。四种模式：Unary、Server Streaming、Client Streaming、Bidirectional Streaming。拦截器：Unary/Stream Interceptor 实现鉴权、日志、链路追踪。Protobuf：二进制序列化，体积小速度快，`.proto` 文件定义服务接口。

## 工程实践

### 错误处理
Go 无异常机制，用 `error` 接口显式处理。`errors.New()` / `fmt.Errorf()` 创建错误。`errors.Is/As` 判断错误链。自定义错误类型实现 `error` 接口。`pkg/errors` 包装错误上下文和堆栈。

### Go 性能优化
- 逃逸分析：减少堆分配，`go build -gcflags="-m"` 查看逃逸
- 对象池：`sync.Pool` 复用对象，减少 GC 压力
- 字符串拼接：`strings.Builder` 优于 `+`
- JSON：`json-iterator` 或 `easyjson` 替代标准库
- pprof：CPU/内存/阻塞分析，`go tool pprof`

### Go 项目结构
`cmd/` 入口、`internal/` 内部包（不可外部引用）、`pkg/` 可复用包、`api/` 接口定义。依赖注入：Wire（编译时）或 fx（运行时）。配置管理：Viper。
