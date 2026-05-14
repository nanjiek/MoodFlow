# MoodFlow 后端开发总结

## 1. 项目范围

本次已完成 MoodFlow 电脑端后端与算法侧整体搭建，覆盖 Django 管理后台后端、FastAPI 模型服务、数据清洗、机器学习 baseline 训练、MLOps 管理能力、Docker 本地环境和测试验证。

## 2. 已完成模块

### 2.1 Django 后端

代码目录：`backend/`

已实现能力：

- 管理员登录与 JWT 鉴权
- 用户管理
- 情绪标签管理
- 情绪记录查询
- 情绪分析结果管理
- 陪伴内容管理
- 系统配置管理
- 情绪树洞内容审核
- 数据统计，包括用户活跃、情绪分布、功能使用、管理员操作日志
- MLOps 管理，包括训练样本、模型版本、推理日志、模型状态

### 2.2 模型服务

代码目录：`model_service/`

已实现能力：

- FastAPI 推理服务
- 情绪预测接口：`POST /predict/emotion`
- 关键词提取接口：`POST /extract/keywords`
- 情绪趋势分析接口：`POST /analyze/trend`
- baseline 模型加载
- 规则兜底预测
- 可选 BERT 微调脚本预留

### 2.3 数据与训练

已完成下载数据集的整合与清洗，生成统一训练集：

```text
data/processed/moodflow_emotions.csv
```

统一映射到 MoodFlow 8 类情绪：

```text
开心 happy
平静 calm
期待 expecting
焦虑 anxious
难过 sad
烦躁 irritable
平淡 plain
疲惫 tired
```

已训练 TF-IDF + Logistic Regression baseline 模型：

```text
model_service/artifacts/baseline/model.joblib
```

模型版本：

```text
baseline-20260513141258
```

训练结果：

```text
样本数：115785
训练集：92628
测试集：23157
accuracy：0.5181
macro F1：0.5643
weighted F1：0.5403
```

### 2.4 Docker 环境

已配置 `docker-compose.yml`，包含：

- MySQL 8
- Redis 7
- Django backend
- FastAPI model-service

### 2.5 文档与脚本

已新增：

- `README.md`：启动与使用说明
- `docs/api_examples.md`：接口调用示例
- `docs/dev_checklist.md`：开发检查清单
- `Makefile`：常用命令入口
- `scripts/`：初始化、训练、健康检查脚本

## 3. 默认管理员账号

```text
username: admin
password: MoodFlow@123456
```

## 4. 常用接口

```text
POST /api/admin/auth/login/
GET  /api/admin/emotions/users/
GET  /api/admin/emotions/records/
GET  /api/admin/emotions/analyses/
GET  /api/admin/statistics/overview/
GET  /api/admin/tree-hole/posts/
GET  /api/admin/mlops/status/
POST /predict/emotion
GET  /health
```

## 5. 本地启动方式

```bash
cp .env.example .env
make train-baseline
make up
make migrate
make seed
make healthcheck
```

## 6. 已验证内容

已完成以下验证：

```text
Django system check：通过
Migration check：通过
Pytest：4 passed
Docker compose config：通过
本地 Django + FastAPI 启动验证：通过
登录接口验证：通过
统计接口验证：通过
模型预测接口验证：通过
```

## 7. 重要说明：数据集不平衡

当前训练集已经完成整合与清洗，但存在明显类别不平衡问题，需要后续补充数据，否则模型对部分类别的识别效果会受影响。

当前数据分布大致如下：

```text
平淡 plain:       49057
开心 happy:       19111
烦躁 irritable:   12520
焦虑 anxious:     11020
平静 calm:         9457
难过 sad:          7589
期待 expecting:    6988
疲惫 tired:          43
```

其中 `疲惫 tired` 严重不足，目前主要依赖少量合成样本；`期待 expecting`、`难过 sad`、`平静 calm` 也建议继续补充。后续如果要提升模型效果，优先补齐这些类别的数据，尤其是疲惫类。

数据补充建议：

```text
P0：疲惫 tired，建议至少补到 1000 条以上，最好补到数千条
P1：期待 expecting、难过 sad、平静 calm
P2：焦虑 anxious、烦躁 irritable
```

当前 baseline 模型测试集 accuracy 约为 `0.5181`，macro F1 约为 `0.5643`。效果不高的主要原因包括：

- 数据标签来源不一致
- 类别分布不均衡
- MoodFlow 的 8 类情绪与公开数据集标签并非完全一一对应
- 疲惫、期待、平静等类别缺少足够贴近产品场景的人工标注数据

后续补充高质量、贴近 MoodFlow 使用场景的人工标注数据后，需要重新训练模型并更新模型版本。

## 8. 深度学习说明

当前在线推理使用轻量机器学习 baseline 模型，已经可以完成基础情绪分类、关键词提取和趋势分析。

深度学习脚本已预留：

```text
model_service/training/train_transformer.py
```

该脚本可用于后续 GPU 环境微调 `bert-base-chinese` 等中文预训练模型。当前 FastAPI 推理服务默认加载：

```text
model_service/artifacts/baseline/model.joblib
```

暂未直接加载 BERT/Hugging Face 训练产物。如需使用深度学习模型上线，需要额外补充 serving adapter。

## 9. 后续建议

建议后续优先处理：

- 补充不平衡类别数据，尤其是 `疲惫 tired`
- 建立人工标注流程，提高标签一致性
- 重新训练 baseline 模型并记录新版本
- 在 GPU 环境中尝试 BERT/RoBERTa 微调
- 为 BERT 模型补充线上推理 adapter
- 根据真实管理后台页面继续细化 API 字段
