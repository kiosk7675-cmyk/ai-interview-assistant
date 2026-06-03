# 数据科学与人工智能面经

## 机器学习基础

### 监督学习 vs 无监督学习 vs 强化学习
- 监督学习：有标签数据，分类（SVM/决策树/随机森林）和回归（线性回归/梯度提升）
- 无监督学习：无标签，聚类（K-Means/DBSCAN）、降维（PCA/t-SNE）、异常检测
- 强化学习：智能体与环境交互，通过奖励信号学习策略（Q-Learning/PPO/SAC）

### 过拟合与欠拟合
过拟合：训练集表现好、测试集差。原因：模型复杂度过高、数据量不足。解决：正则化（L1/L2）、Dropout、数据增强、早停法、交叉验证。
欠拟合：训练集和测试集都差。原因：模型太简单、特征不足。解决：增加模型复杂度、特征工程、减少正则化。

### 偏差-方差权衡
偏差（Bias）：模型预测与真实值的系统性偏差，高偏差=欠拟合。方差（Variance）：模型对不同训练集的敏感程度，高方差=过拟合。模型复杂度增加→偏差降低、方差升高。Bagging 降方差，Boosting 降偏差。

### 常见评估指标
- 分类：Accuracy、Precision（精确率）、Recall（召回率）、F1-Score、AUC-ROC
- 回归：MAE、MSE、RMSE、R²
- 推荐系统：NDCG、Hit Rate、MAP
- 注意：正负样本不平衡时 Accuracy 失效，应看 F1 或 AUC

### 交叉验证
K 折交叉验证：数据分 K 份，每次用 K-1 份训练、1 份验证，取平均。K=5 或 10 常用。时间序列数据用滚动交叉验证（不能随机打散）。留一法（LOO）是 K=N 的特例。

## 深度学习

### 神经网络基础
前向传播：输入×权重+偏置→激活函数→输出。反向传播：链式法则计算梯度，从输出层向输入层传播。激活函数：ReLU（常用，缓解梯度消失）、Sigmoid（二分类输出）、Softmax（多分类输出）、GELU（Transformer 常用）。

### CNN 核心概念
卷积层：局部感受野、权重共享。池化层：最大池化/平均池化，降维+平移不变性。经典架构：LeNet→AlexNet→VGG→ResNet（残差连接解决退化）→EfficientNet。1×1 卷积：降维/升维、跨通道信息融合。

### RNN / LSTM / GRU
RNN：处理序列数据，但存在梯度消失/爆炸。LSTM：遗忘门、输入门、输出门，通过细胞状态缓解长程依赖问题。GRU：LSTM 的简化版，重置门+更新门，参数更少。双向 RNN：同时利用前后文信息。

### Transformer 架构
核心：自注意力机制（Self-Attention），Q/K/V 矩阵计算注意力权重。多头注意力：多组 Q/K/V 并行，捕获不同子空间特征。位置编码：正弦/余弦或可学习。Layer Norm + 残差连接。Encoder-Decoder 结构（原始）、Decoder-only（GPT 系列）、Encoder-only（BERT）。

### 预训练与微调
预训练：大规模无监督数据上学习通用表征（BERT 的 MLM、GPT 的自回归）。微调：在下游任务数据上调整参数。Prompt Tuning / LoRA：冻结大部分参数，只训练少量参数，降低微调成本。

### 生成模型
GAN：生成器与判别器对抗训练，训练不稳定，模式坍塌问题。VAE：变分推断，编码为分布，生成多样性。Diffusion Model：逐步加噪→学习去噪，Stable Diffusion 在 latent space 上操作，当前主流图像生成方法。

## 数据处理

### 特征工程
- 数值型：标准化（Z-Score）、归一化（Min-Max）、分箱、对数变换
- 类别型：独热编码（One-Hot）、标签编码、目标编码（Target Encoding）
- 文本：TF-IDF、Word2Vec、BERT Embedding
- 特征选择：过滤法（相关性）、包裹法（递归特征消除）、嵌入法（L1 正则化）

### 数据清洗
处理缺失值：删除、均值/中位数填充、KNN 填充、模型预测填充。处理异常值：IQR 法、Z-Score 法、孤立森林。数据不平衡：过采样（SMOTE）、欠采样、类别权重调整。

### SQL 数据分析
窗口函数：`ROW_NUMBER() OVER (PARTITION BY ... ORDER BY ...)`、`RANK()`、`LEAD()/LAG()`。聚合：`GROUP BY` + `HAVING`。多表关联：`JOIN`（INNER/LEFT/RIGHT/FULL）。CTE：`WITH ... AS (...)` 提高可读性。

## 工具与框架

### PyTorch vs TensorFlow
PyTorch：动态图，Pythonic 风格，调试方便，学术研究主流。TensorFlow：静态图（2.x 兼容动态），部署生态完善（TF Serving/TF Lite/TF.js）。Keras 是 TF 的高级 API。

### MLOps 流程
数据采集 → 特征工程 → 模型训练 → 评估验证 → 模型部署（A/B 测试/灰度发布）→ 监控（数据漂移/性能衰减）→ 再训练。工具：MLflow（实验跟踪）、Airflow（流水线编排）、ONNX（模型格式转换）。
