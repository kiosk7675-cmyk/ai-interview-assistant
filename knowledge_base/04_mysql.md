# MySQL 数据库

## MySQL 索引原理？
- **B+ 树**：InnoDB 默认索引结构，非叶子节点只存键值，叶子节点存数据+指针，范围查询高效。
- **聚簇索引**：主键索引，叶子节点存完整行数据。一张表只有一个。推荐用自增整型主键。
- **二级索引**：非主键索引，叶子节点存主键值。查询非索引列需回表（先查二级索引再查聚簇索引）。
- **覆盖索引**：查询的列都在索引中，无需回表。`EXPLAIN` 中显示 `Using index`。
- **联合索引**：多个列组合索引，遵循最左前缀原则。`(a, b, c)` 可覆盖 `a`、`a,b`、`a,b,c` 查询。
- **索引下推（ICP）**：MySQL 5.6+，在存储引擎层就根据索引条件过滤，减少回表次数。

## MySQL 事务与 ACID？
- **原子性（A）**：undo log 保证，事务失败可回滚。
- **一致性（C）**：由 A+I+D 共同保证，事务前后数据满足约束。
- **隔离性（I）**：MVCC + 锁保证，不同隔离级别解决不同并发问题。
- **持久性（D）**：redo log 保证，事务提交后数据不丢失（先写 redo log 再写数据文件）。
- **两阶段提交**：redo log prepare → binlog 写入 → redo log commit，保证主从一致性。

## 事务隔离级别？
- **READ UNCOMMITTED**：可读未提交数据，脏读。
- **READ COMMITTED**：只能读已提交数据，不可重复读（Oracle 默认）。
- **REPEATABLE READ**：同一事务内多次读取一致，InnoDB 默认。通过 MVCC 快照读实现。
- **SERIALIZABLE**：完全串行化，性能最差。
- **InnoDB 的 RR 级别**：通过 Next-Key Lock 解决幻读问题（当前读），但快照读仍可能读到旧数据。

## MVCC 原理？
- **隐藏列**：每行有 `trx_id`（最近修改的事务ID）和 `roll_pointer`（指向 undo log）。
- **Read View**：事务开始时创建，记录当前活跃事务列表，判断某个版本是否可见。
- **快照读**：普通 SELECT，通过 Read View 找到可见的版本（undo log 链）。
- **当前读**：SELECT ... FOR UPDATE / INSERT / UPDATE / DELETE，读取最新数据并加锁。
- **RC vs RR**：RC 每次 SELECT 创建新 Read View，RR 只在事务首次 SELECT 创建。

## MySQL 锁机制？
- **共享锁（S）**：读锁，`SELECT ... LOCK IN SHARE MODE`。
- **排他锁（X）**：写锁，`SELECT ... FOR UPDATE`。
- **记录锁**：锁住单行记录。
- **间隙锁（Gap Lock）**：锁住索引间隙，防止插入，解决幻读。
- **Next-Key Lock**：记录锁 + 间隙锁，InnoDB 在 RR 级别的默认行锁算法。
- **意向锁**：表级锁，表示事务打算加行锁，快速判断表级冲突。
- **死锁**：两个事务互相等待对方持有的锁。InnoDB 自动检测，回滚代价小的事务。

## SQL 优化实战？
- **EXPLAIN**：查看执行计划，关注 type（ALL=全表扫描）、key（使用索引）、rows（扫描行数）、Extra。
- **避免全表扫描**：WHERE 条件列建索引，避免 `LIKE '%xxx'`、函数操作、隐式类型转换。
- **分页优化**：`LIMIT 100000, 10` 很慢，改用 `WHERE id > 100000 LIMIT 10`（游标分页）。
- **COUNT 优化**：`COUNT(*)` 优于 `COUNT(列)`，InnoDB 的 COUNT 需要遍历二级索引。
- **批量操作**：批量 INSERT 用 `INSERT INTO ... VALUES (),(),()`，减少事务次数。
- **索引失效场景**：OR 条件（部分列无索引）、!= / <>、IS NOT NULL、列计算、类型不匹配。

## 数据库连接池？
- **为什么需要**：创建连接开销大（TCP 三次握手 + 权限验证 + 字符集协商），复用连接减少开销。
- **核心参数**：min_size（最小连接数）、max_size（最大连接数）、max_idle_time（空闲超时）。
- **Python 连接池**：SQLAlchemy 的 `create_engine(pool_size=10, max_overflow=20)`。
- **监控指标**：活跃连接数、空闲连接数、等待连接的请求数、连接平均使用时间。

## 分库分表？
- **垂直拆分**：按业务模块拆分数据库（用户库、订单库、商品库）。
- **水平拆分**：同一表数据按规则分散到多张表（如按用户 ID 取模）。
- **分片键选择**：高频查询条件、数据分布均匀、避免跨分片查询。
- **问题**：跨分片 JOIN、分布式事务、全局 ID、数据迁移。
- **中间件**：ShardingSphere、MyCat，或应用层分片。
