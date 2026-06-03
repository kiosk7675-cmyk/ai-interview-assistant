# Python 核心基础

## Python 的 GIL 是什么？对多线程有什么影响？
GIL（Global Interpreter Lock，全局解释器锁）是 CPython 中的一个互斥锁，确保同一时刻只有一个线程执行 Python 字节码。
- **CPU 密集型**：多线程无法真正并行，甚至比单线程更慢（线程切换开销）。应使用 multiprocessing 或 C 扩展绕过 GIL。
- **I/O 密集型**：多线程有效，因为线程在等待 I/O 时会释放 GIL，其他线程可以执行。
- **Python 3.2+**：GIL 的切换策略从基于 tick 改为基于时间（默认 5ms），减少了线程饥饿问题。
- **nogil 项目（PEP 703）**：Python 3.13 已引入实验性的 free-threaded 模式，可禁用 GIL。

## Python 可变类型与不可变类型的区别？
- **不可变**：int, float, str, tuple, frozenset, bytes。修改时创建新对象。
- **可变**：list, dict, set, bytearray。原地修改，id 不变。
- **陷阱**：函数默认参数用可变对象（如 `def f(a=[])`），多次调用共享同一对象，应改用 `None` + 内部初始化。
- **元组不是完全不可变**：元组内如果包含可变对象（如 list），该可变对象的内容仍可修改。

## Python 的深拷贝与浅拷贝？
- **浅拷贝**：`copy.copy()` 或 `list()` 或切片 `[:]`，只复制第一层，嵌套对象仍是引用。
- **深拷贝**：`copy.deepcopy()`，递归复制所有层级，完全独立。
- **注意**：深拷贝会处理循环引用，但开销较大。

## Python 装饰器的原理和应用场景？
装饰器本质是一个高阶函数，接受函数作为参数并返回新函数。语法糖 `@decorator` 等价于 `func = decorator(func)`。
- **无参数装饰器**：`def log(func): def wrapper(*args, **kw): ...; return wrapper`
- **带参数装饰器**：需要三层嵌套：`def log(text): def decorator(func): def wrapper(*a, **kw): ...; return wrapper; return decorator`
- **functools.wraps**：必须使用，保留原函数的 `__name__`、`__doc__` 等元信息。
- **类装饰器**：实现 `__call__` 方法的类，可维护状态。
- **应用场景**：日志记录、权限校验、缓存（lru_cache）、重试机制、计时统计、事务管理。

## Python 的生成器和迭代器？
- **迭代器协议**：实现 `__iter__()` 返回 self 和 `__next__()` 返回下一个值或抛出 StopIteration。
- **生成器**：用 `yield` 的函数，调用时返回生成器对象（迭代器的一种）。惰性求值，节省内存。
- **生成器表达式**：`(x*x for x in range(10))`，比列表推导式更省内存。
- **yield from**：委托给子生成器，简化嵌套生成器写法。
- **send() 方法**：向生成器内部传值，实现协程的基础。

## Python 的上下文管理器？
- **协议**：实现 `__enter__()` 和 `__exit__(exc_type, exc_val, exc_tb)`。
- **with 语句**：保证 `__exit__` 一定会被调用，即使发生异常。
- **contextlib.contextmanager**：用生成器简化上下文管理器编写。
- **contextlib.closing**：包装有 close() 方法的对象。
- **应用场景**：文件操作、数据库连接、锁的获取释放、临时修改环境变量。

## Python 的 *args 和 **kwargs？
- **`*args`**：收集多余的位置参数为元组。
- **`**kwargs`**：收集多余的关键字参数为字典。
- **解包**：`func(*list)` 解包列表，`func(**dict)` 解包字典为关键字参数。
- **混合使用**：`def f(a, b, *args, key=None, **kwargs)`，位置参数 → *args → 关键字参数 → **kwargs。
- **仅关键字参数**：`def f(a, *, key)` 强制 key 必须用关键字传入。

## Python 的类方法、静态方法、实例方法？
- **实例方法**：第一个参数为 self，可访问实例属性和类属性。
- **类方法**：`@classmethod`，第一个参数为 cls，常用于工厂方法（替代构造函数）。
- **静态方法**：`@staticmethod`，不需要 self/cls，与类逻辑相关但不需要访问类/实例状态。
- **实际应用**：类方法做工厂模式（如 `from_dict`），静态方法做工具函数（如日期格式校验）。

## Python 的 __new__ 和 __init__ 的区别？
- **`__new__`**：创建实例（分配内存），是类方法，返回实例对象。在 `__init__` 之前调用。
- **`__init__`**：初始化实例（设置属性），是实例方法，无返回值。
- **单例模式**：在 `__new__` 中控制只创建一次实例。
- **不可变类型**：str/int/tuple 的子类化必须在 `__new__` 中处理，因为 `__init__` 无法修改不可变对象的值。

## Python 的垃圾回收机制？
- **引用计数**：主要机制，对象引用数为 0 时立即回收。缺点：无法处理循环引用。
- **标记-清除（mark-and-sweep）**：解决循环引用，定期扫描容器对象（list/dict/set/tuple/class 等）。
- **分代回收**：三代（0/1/2），新对象在 0 代，存活过 GC 的晋升到下一代。年轻代回收更频繁。
- **gc 模块**：`gc.get_count()` 查看计数，`gc.collect()` 手动触发，`gc.disable()` 禁用自动 GC。
- **弱引用**：`weakref.ref()` 不增加引用计数，常用于缓存。

## Python 的鸭子类型和类型注解？
- **鸭子类型**：不关心对象类型，只关心行为（方法/属性）。"如果它走起来像鸭子，叫起来像鸭子，那它就是鸭子"。
- **类型注解**：Python 3.5+ 支持，`def greet(name: str) -> str:`，不影响运行时，供 mypy 等工具检查。
- **typing 模块**：List, Dict, Optional, Union, Literal, TypedDict, Protocol 等。
- **Protocol（结构化子类型）**：Python 3.8+，定义接口不要求显式继承，比 ABC 更灵活。
