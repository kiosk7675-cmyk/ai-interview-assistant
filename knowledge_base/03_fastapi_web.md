# FastAPI 与 Web 框架

## FastAPI 的核心特性？
- **高性能**：基于 Starlette（ASGI 框架）和 Pydantic（数据验证），性能接近 Go/Node.js。
- **自动文档**：基于 OpenAPI 规范自动生成 Swagger UI 和 ReDoc 文档。
- **类型注解驱动**：利用 Python 类型注解做参数验证、序列化、文档生成。
- **异步原生**：天然支持 async/await，ASGI 协议。
- **依赖注入**：`Depends()` 声明式依赖，支持嵌套和作用域。

## FastAPI 的请求生命周期？
1. 客户端发送 HTTP 请求
2. ASGI 服务器（uvicorn）接收请求
3. Starlette 中间件处理（CORS、认证等）
4. 路由匹配找到对应的路径操作函数
5. 依赖注入解析（数据库会话、当前用户等）
6. Pydantic 验证请求参数（路径参数、查询参数、请求体）
7. 执行业务逻辑
8. Pydantic 序列化响应模型
9. 中间件后处理
10. 返回 HTTP 响应

## WSGI vs ASGI？
- **WSGI**：同步协议，一个请求一个线程，如 Gunicorn + Flask/Django。不支持 WebSocket、SSE。
- **ASGI**：异步协议，一个连接可以处理多个事件（HTTP、WebSocket、SSE），如 Uvicorn + FastAPI。
- **兼容**：ASGI 服务器可以运行 WSGI 应用（通过适配器），反之不行。

## Pydantic 的核心用法？
- **BaseModel**：定义数据模型，自动类型校验和转换。`model.model_dump()` 序列化，`Model(**data)` 反序列化。
- **Field**：字段约束，`Field(ge=0, le=100, description="年龄")`。
- **嵌套模型**：模型中引用其他模型，自动递归验证。
- **自定义验证器**：`@field_validator('email')` 或 `@model_validator(mode='after')`。
- **ConfigDict**：`from_attributes=True` 支持 ORM 对象转换，`str_strip_whitespace=True` 自动去空格。
- **v2 性能**：Pydantic v2 用 Rust 重写核心，比 v1 快 5-50 倍。

## FastAPI 依赖注入详解？
- **基本用法**：`db: Session = Depends(get_db)`，函数参数声明依赖。
- **全局依赖**：`app = FastAPI(dependencies=[Depends(verify_token)])`。
- **嵌套依赖**：依赖函数本身可以有依赖，自动递归解析。
- **yield 依赖**：`def get_db(): db = Session(); yield db; db.close()`，实现资源清理。
- **作用域**：默认每次请求创建新实例，`app.state` 可存应用级状态。

## FastAPI 中间件？
- **CORS**：`CORSMiddleware(allow_origins, allow_methods, allow_headers)`，生产环境应限制 origins。
- **自定义中间件**：`@app.middleware("http")`，在请求前后添加逻辑。
- **执行顺序**：中间件按注册顺序"洋葱式"嵌套，先注册的最外层。
- **注意**：中间件中不能抛 HTTPException，需要用 `return JSONResponse` 代替。

## FastAPI 的认证与授权？
- **OAuth2PasswordBearer**：从请求头提取 Bearer Token。
- **JWT**：`python-jose` 库，Token = Header.Payload.Signature，无状态认证。
- **密码哈希**：`passlib[bcrypt]`，`pwd_context.hash(plain)` / `pwd_context.verify(plain, hashed)`。
- **权限控制**：依赖注入 + 角色校验，`Depends(get_current_user)` + `Depends(require_admin)`。

## RESTful API 设计规范？
- **资源命名**：名词复数，如 `/users`、`/articles`。
- **HTTP 方法**：GET 查询、POST 创建、PUT 全量更新、PATCH 部分更新、DELETE 删除。
- **状态码**：200 成功、201 创建、204 删除成功、400 请求错误、401 未认证、403 无权限、404 不存在、422 验证失败、500 服务器错误。
- **分页**：`?page=1&size=20`，返回 `total`、`items`、`page`、`size`。
- **过滤排序**：`?status=active&sort=-created_at`（- 表示降序）。
- **HATEOAS**：响应中包含相关链接，实践中较少使用。

## FastAPI 的异常处理？
- **HTTPException**：`raise HTTPException(status_code=404, detail="Not found")`。
- **自定义异常处理器**：`@app.exception_handler(CustomError)`，统一错误格式。
- **请求验证错误**：422 Unprocessable Entity，Pydantic 自动处理，可自定义格式。
- **全局异常**：捕获所有 Exception 返回 500，避免暴露内部错误信息。

## Nginx 反向代理配置？
- **作用**：负载均衡、静态文件服务、SSL 终止、限流、跨域。
- **配置要点**：`proxy_pass http://127.0.0.1:8000;`，`proxy_set_header Host $host;`，`proxy_set_header X-Real-IP $remote_addr;`
- **WebSocket**：需要 `proxy_set_header Upgrade $http_upgrade;` 和 `Connection "upgrade";`。
- **SSE**：需要 `proxy_buffering off;` 和 `proxy_cache off;`，否则 Nginx 会缓冲 SSE 流。
