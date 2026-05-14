# API Examples

默认本地地址：

- Backend: `http://localhost:8000`
- Model service: `http://localhost:8010`

## 管理员登录

当前路由挂载后，登录地址为 `/api/admin/auth/login/`。

```bash
curl -X POST http://localhost:8000/api/admin/auth/login/ \
  -H 'Content-Type: application/json' \
  -d '{
    "username": "admin",
    "password": "MoodFlow@123456"
  }'
```

```json
{
  "token": "<jwt-token>",
  "token_type": "Bearer",
  "expires_at": "2026-05-13T16:00:00+08:00",
  "profile": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "role": "super_admin",
    "status": "active"
  }
}
```

## 用户列表

```bash
curl 'http://localhost:8000/api/admin/emotions/users/?page=1&page_size=20' \
  -H 'Authorization: Bearer <jwt-token>'
```

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 10,
      "user": 3,
      "user_detail": {
        "id": 3,
        "external_id": "demo-user-001",
        "nickname": "小澄",
        "avatar_url": ""
      },
      "emotion_text": "今天完成了一个小目标，很开心。",
      "tag": 1,
      "recorded_at": "2026-05-13T10:00:00+08:00"
    }
  ]
}
```

## 统计

情绪分析结果列表：

```bash
curl 'http://localhost:8000/api/admin/emotions/analyses/?page=1&page_size=20' \
  -H 'Authorization: Bearer <jwt-token>'
```

趋势统计可以调用模型服务：

```bash
curl -X POST http://localhost:8010/analyze/trend \
  -H 'Content-Type: application/json' \
  -d '{
    "records": [
      {"label": "anxious"},
      {"label": "anxious"},
      {"label": "sad"},
      {"predicted_label": "tired"}
    ]
  }'
```

```json
{
  "trend": "negative_rising",
  "summary": "最近记录中出现最多的是焦虑。 近 7 条记录里负向情绪偏多，建议优先推送呼吸放松或低刺激陪伴内容。",
  "dominant_label": "anxious",
  "negative_days": 4
}
```

## 审核

待审核树洞列表：

```bash
curl 'http://localhost:8000/api/admin/tree-hole/posts/?status=pending&page=1&page_size=20' \
  -H 'Authorization: Bearer <jwt-token>'
```

通过审核：

```bash
curl -X POST http://localhost:8000/api/admin/tree-hole/posts/12/approve/ \
  -H 'Authorization: Bearer <jwt-token>'
```

驳回审核：

```bash
curl -X POST http://localhost:8000/api/admin/tree-hole/posts/12/reject/ \
  -H 'Authorization: Bearer <jwt-token>' \
  -H 'Content-Type: application/json' \
  -d '{"reason":"包含不适合公开展示的内容"}'
```

## 模型预测

```bash
curl -X POST http://localhost:8010/predict/emotion \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "今天压力很大，心里一直很紧张",
    "selected_label": "anxious",
    "user_id": "demo-user-001"
  }'
```

```json
{
  "label": "anxious",
  "label_name": "焦虑",
  "category": "negative",
  "confidence": 0.8123,
  "intensity": 0.9123,
  "keywords": ["压力", "紧张"],
  "model_version": "baseline-untrained",
  "probabilities": {
    "happy": 0.02,
    "calm": 0.02,
    "expecting": 0.02,
    "anxious": 0.81,
    "sad": 0.04,
    "irritable": 0.03,
    "plain": 0.02,
    "tired": 0.04
  }
}
```

## 训练脚本命令

构建训练集：

```bash
PYTHONPATH=. python -m model_service.training.dataset_builder \
  --raw-dir data/raw \
  --output data/processed/moodflow_emotions.csv
```

训练 baseline 模型：

```bash
PYTHONPATH=. python -m model_service.training.train_baseline \
  --dataset data/processed/moodflow_emotions.csv \
  --output-dir model_service/artifacts/baseline
```

启动模型服务后，`/health` 的 `model_ready` 会反映模型文件是否已加载。
