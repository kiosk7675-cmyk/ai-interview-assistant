# Python 异步编程

## async/await 的原理？
- **协程**：用 `async def` 定义的函数，调用时返回协程对象，不会立即执行。
- **事件循环（Event Loop）**：asyncio 的核心，负责调度协程的执行、I/O 回调、定时器。
- **await**：挂起当前协程，将控制权交还事件循环，等待 awaitable 完成后恢复执行。
- **可等待对象**：协程、Task、Future 都实现了 `__await__()` 协议。

## asyncio 的核心组件？
- **event_loop**：事件循环，`asyncio.get_event_loop()` 或 `asyncio.run()`。
- **Task**：对协程的封装，`asyncio.create_task()` 可并发调度多个协程。
- **Future**：表示未来某个时刻的结果，Task 是 Future 的子类。
- **asyncio.gather()**：并发运行多个协程，等待全部完成，返回结果列表。
- **asyncio.wait()**：更灵活，可指定 FIRST_COMPLETED/FIRST_EXCEPTION 等策略。

## 同步 vs 异步的使用场景？
- **异步适合**：大量 I/O 操作（HTTP 请求、数据库查询、文件读写、WebSocket）。
- **同步适合**：CPU 密集型计算、简单的脚本、不需要并发的场景。
- **混合使用**：`asyncio.to_thread()` 将阻塞 I/O 放到线程池；`loop.run_in_executor()` 调用同步函数。
- **FastAPI**：天然支持 async，路由函数用 `async def` 定义即可自动异步处理。

## 异步编程的常见陷阱？
1. **在 async 函数中调用阻塞函数**：如 `requests.get()`、`time.sleep()`，会阻塞整个事件循环。应替换为 `httpx.AsyncClient`、`asyncio.sleep()`。
2. **忘记 await**：`coroutine()` 不加 await 不会执行，只会创建协程对象。Python 3.11+ 会发出 RuntimeWarning。
3. **创建 Task 不等待**：`asyncio.create_task()` 后如果不保存引用，Task 可能被 GC 回收而消失。
4. **竞态条件**：多个协程操作共享状态时仍需锁（`asyncio.Lock`）。
5. **异常丢失**：Task 中的异常如果不 `await` 或 `result()` 获取，会静默忽略。

## 异步数据库和 ORM？
- **asyncpg**：PostgreSQL 异步驱动，性能极高。
- **aiomysql / aioredis**：MySQL 和 Redis 的异步驱动。
- **SQLAlchemy 2.0**：原生支持 async，`async_session` + `await session.execute()`。
- **Tortoise ORM**：Django 风格的异步 ORM。
- **连接池**：异步场景必须用连接池管理数据库连接，避免频繁创建销毁。

## FastAPI 中的异步最佳实践？
- 路由函数尽量用 `async def`，FastAPI 自动在事件循环中调度。
- 如果路由中有阻塞调用（如同步 ORM），用 `def` 而非 `async def`，FastAPI 会自动放到线程池执行。
- 中间件和依赖注入也支持 async。
- 后台任务：`BackgroundTasks` 或 `asyncio.create_task()`。
- SSE（Server-Sent Events）：使用 `sse-starlette` 库，用 `async generator` 推送数据。

## Python 多线程 vs 多进程 vs 异步？
- **多线程（threading）**：受 GIL 限制，CPU 密集型无法并行。适合 I/O 密集型。线程切换开销小。
- **多进程（multiprocessing）**：绕过 GIL，每个进程独立 GIL。CPU 密集型首选。进程创建和通信开销大。
- **异步（asyncio）**：单线程内通过事件循环调度，无锁、无 GIL 问题。I/O 密集型最优。但需要整个调用链都是 async 的。
- **选择策略**：CPU 密集 → 多进程；I/O 密集且调用链可控 → asyncio；I/O 密集但有大量同步库 → 多线程。

## 信号量与限流？
- **asyncio.Semaphore**：限制同时执行的协程数量，实现并发限流。
- **令牌桶算法**：控制请求速率，FastAPI 中可用中间件实现。
- **aiolimiter**：异步速率限制库，基于令牌桶。
