# Java 后端开发面经

## Java 基础

### Java 与 C++ 的区别
Java 是纯面向对象语言（基本类型除外），不支持指针、多继承、运算符重载。JVM 提供垃圾回收和跨平台能力，C++ 需要手动管理内存。Java 有完善的异常处理体系和反射机制。

### == 与 equals 的区别
`==` 比较引用地址（基本类型比较值），`equals()` 比较内容。String 的 `equals()` 已被重写为逐字符比较。自定义类需重写 `equals()` 和 `hashCode()`，且保证等价对象的 hashCode 一致。

### HashMap 原理
JDK 1.8 中 HashMap 采用数组+链表+红黑树结构。初始容量 16，负载因子 0.75。put 时根据 key 的 hash 值计算桶位，发生碰撞时链表插入（尾插法，避免死链）。链表长度 ≥8 且数组长度 ≥64 时转红黑树。扩容时容量翻倍，rehash 重新分布。

### ConcurrentHashMap 线程安全
JDK 1.8 放弃分段锁，改用 CAS + synchronized。put 时如果桶为空用 CAS 写入；如果非空对头节点加 synchronized 锁。扩容时多线程协助迁移数据，提高效率。

### JVM 内存模型
- 堆：对象实例、数组，GC 主要区域，分为新生代（Eden + S0 + S1）和老年代
- 方法区/元空间：类信息、常量池、静态变量
- 虚拟机栈：栈帧（局部变量表、操作数栈、动态链接、方法出口）
- 本地方法栈：Native 方法
- 程序计数器：当前执行的字节码行号

### 垃圾回收算法与收集器
- 标记-清除：产生碎片
- 标记-整理：移动对象，无碎片但开销大
- 复制算法：新生代用，Eden→Survivor 复制
- 分代收集：新生代用复制，老年代用标记-整理
- 常用收集器：CMS（低延迟，标记-清除）、G1（Region 化，可预测停顿）、ZGC（染色指针，<1ms 停顿）

### 类加载机制
双亲委派模型：Bootstrap → Extension → Application ClassLoader。加载类时先委托父加载器，防止核心类被篡改。打破双亲委派的场景：SPI 机制（JDBC）、Tomcat 类隔离、OSGi 模块化。

## Spring 生态

### Spring IoC 与 AOP
IoC（控制反转）：通过 DI（依赖注入）将对象创建和管理交给容器。方式有构造器注入、Setter 注入、字段注入（@Autowired）。推荐构造器注入，保证不可变性和依赖完整性。

AOP（面向切面）：基于动态代理（JDK 代理接口 / CGLIB 代理类）。核心概念：切面（@Aspect）、切入点（@Pointcut）、通知（@Before/@After/@Around）。应用：日志、事务、权限校验。

### Spring Bean 生命周期
实例化 → 属性赋值 → Aware 回调 → BeanPostProcessor.postProcessBeforeInitialization → InitializingBean.afterPropertiesSet → @PostConstruct → init-method → BeanPostProcessor.postProcessAfterInitialization → 使用 → DisposableBean.destroy → @PreDestroy → destroy-method

### Spring Boot 自动配置原理
`@SpringBootApplication` 包含 `@EnableAutoConfiguration`。通过 `SpringFactoriesLoader` 加载 `META-INF/spring.factories` 中的配置类。`@Conditional` 系列注解（@ConditionalOnClass、@ConditionalOnMissingBean）决定是否生效。

### Spring 事务传播行为
- REQUIRED（默认）：有事务加入，无事务新建
- REQUIRES_NEW：始终新建事务，挂起当前事务
- NESTED：嵌套事务，外层回滚内层也回滚
- NOT_SUPPORTED：非事务执行，挂起当前事务
- NEVER：非事务执行，存在事务则抛异常

### MyBatis 与 Hibernate 对比
MyBatis：半自动 ORM，SQL 手写灵活，适合复杂查询优化。支持动态 SQL（if/foreach/where）。Hibernate：全自动 ORM，HQL 跨数据库，但复杂查询性能难控。面试重点：MyBatis #{} 和 ${} 的区别——#{} 预编译防 SQL 注入，${} 字符串拼接有注入风险。

## 微服务

### Spring Cloud 核心组件
- 服务注册与发现：Nacos / Eureka
- 配置中心：Nacos Config / Spring Cloud Config
- 网关：Spring Cloud Gateway（基于 WebFlux）
- 负载均衡：Spring Cloud LoadBalancer
- 熔断降级：Sentinel / Resilience4j
- 链路追踪：SkyWalking / Zipkin

### 分布式事务
- 2PC（两阶段提交）：XA 协议，强一致但阻塞
- TCC：Try-Confirm-Cancel，业务侵入，最终一致
- SAGA：长事务编排，补偿机制
- 本地消息表 + MQ：可靠消息最终一致
- Seata：AT 模式（自动回滚）、TCC 模式、SAGA 模式

### 服务熔断与降级
熔断器模式：Closed → Open（错误率超阈值）→ Half-Open（试探性放行）。Sentinel 支持流控、熔断、热点限流、系统保护。降级策略：返回默认值、缓存数据、写入 MQ 延后处理。
