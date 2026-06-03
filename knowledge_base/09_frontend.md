# 前端开发面经

## HTML / CSS

### HTML5 新特性
语义化标签（header/nav/article/section/footer）、Canvas/WebGL 绘图、音视频标签、Web Storage（localStorage/sessionStorage）、Web Workers 多线程、Geolocation 定位、WebSocket 双向通信、拖放 API。

### CSS 盒模型
标准盒模型：width = content 宽度。IE 盒模型：width = content + padding + border。通过 `box-sizing: border-box` 切换为 IE 盒模型。margin 不计入盒模型宽度，但影响元素占位。

### Flex 与 Grid 布局
Flex：一维布局，`display: flex`，主轴/交叉轴，`justify-content` / `align-items` 控制对齐，`flex: 1` 自动填充剩余空间。
Grid：二维布局，`display: grid`，`grid-template-columns/rows` 定义行列，`grid-area` 命名区域布局。

### BFC（块级格式化上下文）
BFC 是独立的渲染区域，内部元素不影响外部。触发条件：`overflow: hidden`、`display: flow-root`、`float`、`position: absolute/fixed`。应用：清除浮动、防止 margin 重叠、自适应布局。

### CSS 选择器优先级
!important > 内联样式(1000) > ID(100) > 类/伪类/属性(10) > 元素/伪元素(1) > 通配符(0)。相同优先级后写覆盖前写。

## JavaScript

### 数据类型与类型判断
基本类型：number/string/boolean/null/undefined/symbol/bigint。引用类型：object/function/array。
- `typeof`：判断基本类型，typeof null === 'object'（历史 bug）
- `instanceof`：判断原型链
- `Object.prototype.toString.call()`：最准确，返回 `[object Xxx]`

### 闭包
闭包是函数与其词法作用域的组合。内部函数引用外部函数的变量，外部函数执行完毕后变量不会释放。应用：数据私有化、柯里化、防抖节流。风险：内存泄漏（循环引用、未解除事件监听）。

### 原型链
每个对象有 `__proto__` 指向其构造函数的 `prototype`。属性查找沿原型链向上，直到 `null`。`Object.create(obj)` 创建以 obj 为原型的对象。ES6 `class` 是原型继承的语法糖。

### 事件循环
宏任务：setTimeout/setInterval/I/O/UI 渲染。微任务：Promise.then/MutationObserver/queueMicrotask。执行顺序：同步代码 → 清空微任务队列 → 一个宏任务 → 清空微任务 → 下一个宏任务。`async/await` 是 Generator + Promise 的语法糖，await 后面的代码相当于 `.then()`。

### Promise
三种状态：pending → fulfilled / rejected（不可逆）。`.then()` 返回新 Promise 支持链式调用。`Promise.all()` 全部成功才成功，一个失败即失败。`Promise.race()` 取最先完成的。`Promise.allSettled()` 等所有完成。`Promise.any()` 取最先成功的。

### ES6+ 新特性
let/const 块级作用域、箭头函数（无 this/arguments）、解构赋值、模板字符串、扩展运算符、Map/Set、Symbol、Proxy/Reflect、可选链 `?.`、空值合并 `??`。

## 框架

### Vue 3 核心变化
- Composition API：`setup()` / `ref()` / `reactive()` / `computed()` / `watch()`
- 响应式：Proxy 替代 Object.defineProperty，支持动态属性和数组索引
- Fragment：模板支持多根节点
- Teleport：传送门，弹窗挂载到 body
- 更好的 TypeScript 支持

### React Hooks
`useState`：状态管理。`useEffect`：副作用（替代 componentDidMount/Update/Unmount）。`useCallback/useMemo`：性能优化，缓存函数/计算结果。`useRef`：持久引用（DOM 或可变值）。`useContext`：跨组件状态共享。

Rules of Hooks：只在顶层调用、只在函数组件或自定义 Hook 中调用。

### Virtual DOM 与 Diff 算法
虚拟 DOM 是 JS 对象描述真实 DOM。更新时先对比新旧虚拟 DOM（Diff），再最小化更新真实 DOM。React Diff 策略：同层比较、不同类型直接替换、列表用 key 优化。Vue 3 的 PatchFlag 编译时标记动态节点，跳过静态对比。

### 状态管理
- Vue：Pinia（推荐，TS 友好，去掉了 Vuex 的 mutations）
- React：Redux Toolkit（immutable state）、Zustand（轻量）、Jotai/Recoil（原子化）

### 前端路由
Hash 路由：`#` 后变化触发 `hashchange`，兼容性好。History 路由：`pushState/replaceState` + `popstate`，需要后端配合（Nginx try_files）。Vue Router / React Router 都支持两种模式。

## 工程化

### Webpack vs Vite
Webpack：bundle 打包，开发时全量构建，HMR 需重新打包模块链。Vite：开发时基于 ESM 原生 import，按需编译，冷启动极快；生产用 Rollup 打包。

### 性能优化
- 加载：代码分割（lazy/Suspense）、Tree Shaking、图片懒加载、CDN、Gzip/Brotli
- 渲染：虚拟列表、防抖节流、requestAnimationFrame、CSS will-change
- 缓存：HTTP 强缓存/协商缓存、Service Worker、localStorage
- 指标：FCP/LCP/FID/CLS（Core Web Vitals）
