# MoodFlow

MoodFlow 后端项目由 Django 后端、FastAPI 模型服务、MySQL 8 和 Redis 7 组成。当前仓库已提供根目录基础设施，服务代码由对应目录的 `backend/Dockerfile` 与 `model_service/Dockerfile` 构建。

## 本地启动

1. 准备环境变量：

   ```bash
   cp .env.example .env
   ```

2. 启动全部服务：

   ```bash
   make up
   ```

3. 初始化数据库和数据：

   ```bash
   make migrate
   make train-baseline
   make seed
   ```

常用命令：

```bash
make logs          # 查看服务日志
make down          # 停止服务
make run-backend   # 单独运行 Django 开发服务
make run-model     # 单独运行 FastAPI 模型服务
make test          # 运行测试
make lint          # Python compileall 轻量检查
```

## 训练基线模型

默认训练入口为：

```bash
make train-baseline
```

训练会把 `data/raw/` 下的数据归一化为 `data/processed/moodflow_emotions.csv`，并输出模型到 `model_service/artifacts/baseline/`。

## 访问接口

- Django backend: <http://localhost:8000>
- FastAPI model-service: <http://localhost:8010>
- FastAPI docs: <http://localhost:8010/docs>
- MySQL: `localhost:3306`，数据库/用户/密码均为 `moodflow`
- Redis: `localhost:6379`

启动后可执行：

```bash
make healthcheck
```

默认 seed 后的管理员账号：

- 用户名：`admin`
- 密码：`MoodFlow@123456`

常用后台接口：

- `POST /api/admin/auth/login/`
- `GET /api/admin/emotions/users/`
- `GET /api/admin/statistics/overview/`
- `GET /api/admin/tree-hole/posts/`
- `GET /api/admin/mlops/status/`

## 数据目录

原始数据位于 `data/raw/`，当前包括中文多情绪对话数据、SMP2020-EWECT 数据和 CPED 数据。Docker Compose 会以只读方式挂载 `./data` 到服务容器的 `/app/data`。
