# MoodFlow

MoodFlow 是一个包含 Django 后端、FastAPI 模型服务和 Expo 移动端的情绪记录与分析项目。当前仓库已经整理成一套可本地联调、可在 Expo 中继续调试、并保留后续 Android APK 打包能力的结构。

## 当前推荐配置

### 后端与模型服务

- Django backend
- FastAPI model-service
- MySQL 8
- Redis 7

### 移动端

- Expo + TypeScript + Expo Router
- 当前保留为 **Expo SDK 52**
- 主要用于后续界面和流程调试

### 当前默认模型

当前保留的主模型版本为：

- `model_service/artifacts/baseline-clean-v4/`

## 快速开始

### 1. 准备根目录环境变量

项目根目录需要 `.env`：

```powershell
Copy-Item .env.example .env
```

如果仓库里已经有 `.env`，可直接沿用。

### 2. 启动后端服务

推荐直接使用 Docker Compose：

```powershell
cd MoodFlow-main
docker compose up -d --build
```

初始化数据库和种子数据时，可按需执行：

```powershell
docker compose exec backend python manage.py migrate
docker compose run --rm backend sh -c "python manage.py seed_admin && python manage.py seed_emotions && python manage.py seed_content && python manage.py seed_tree_holes && python manage.py seed_usage_logs && python manage.py seed_model_versions"
```

如果项目里保留 `Makefile`，也可以继续使用 `make` 命令；但在 Windows 本机环境中，`docker compose` 更直接。

### 3. 启动移动端 Expo 调试

在 `mobile` 目录下：

```powershell
cd mobile
npm install
npm run start
```

## 两种部署 / 调试方式

当前项目推荐区分为两条路径：

### 1. Expo 调试路径

适合：

- 页面联调
- 主流程验证
- 快速真机预览
- 文案、交互、样式调整

特点：

- 修改快
- 不需要每次都重新打包
- 适合开发期反复迭代

详细说明见：

- [docs/expo_debug_setup.md](./docs/expo_debug_setup.md)

### 2. Android APK 路径

适合：

- 真正安装到 Android 手机上测试
- 验证独立安装包行为
- 验证 EAS / Firebase / FCM 这类原生依赖
- 为后续提交成果、交给他人安装体验做准备

特点：

- 需要通过 EAS 重新构建
- 每次改动后建议递增版本号再打包
- 更接近最终交付形态

详细说明见：

- [docs/android_packaging_checklist.md](./docs/android_packaging_checklist.md)

## 移动端运行配置

建议在 `mobile/.env` 中配置局域网地址：

```bash
EXPO_PUBLIC_API_BASE_URL=http://你的电脑局域网IP:8000
EXPO_PUBLIC_MODEL_BASE_URL=http://你的电脑局域网IP:8010
```

例如：

```bash
EXPO_PUBLIC_API_BASE_URL=http://<your-lan-ip>:8000
EXPO_PUBLIC_MODEL_BASE_URL=http://<your-lan-ip>:8010
```

说明：

- 手机真机不能访问电脑上的 `localhost`
- 同一局域网下应使用电脑局域网 IP
- 当前移动端主要通过 Django backend 调用业务接口
- 如果你是在**自己的电脑**上启动 backend / model-service，请把这里的 `http://<your-lan-ip>:8000` 和 `http://<your-lan-ip>:8010` 替换成你自己电脑的局域网 IP
- 例如你的电脑在局域网中的地址如果是 `192.168.0.23`，那么应改成：

```bash
EXPO_PUBLIC_API_BASE_URL=http://192.168.0.23:8000
EXPO_PUBLIC_MODEL_BASE_URL=http://192.168.0.23:8010
```

如果需要打 Android APK，请注意：

- 本地 `mobile/.env` 只适合 Expo 联调
- **EAS 远程构建不会依赖你本机未提交的 `.env` 文件**
- 当前项目已经将 `preview` / `production` 构建需要的 API 地址写入 [mobile/eas.json](./mobile/eas.json)
- 由于当前仓库是在一台本地电脑上联调并完成 APK 打包验证的，`mobile/eas.json` 中保留了当时的局域网 IP 作为构建环境变量
- 如果你在**另一台电脑**上继续打包，请先打开 [mobile/eas.json](./mobile/eas.json)，把其中的：
  - `EXPO_PUBLIC_API_BASE_URL`
  - `EXPO_PUBLIC_MODEL_BASE_URL`
  改成你自己电脑对应的局域网 IP
- 否则打出来的 APK 仍然会去请求旧机器的地址，导致登录、注册等接口无法连接

## Expo 调试说明

当前项目保留 Expo，主要用于：

- 页面调试
- 交互联调
- 主流程验证
- 真机预览

当前**不把 Expo 预览作为消息推送最终验证环境**。虽然仓库中保留了 Firebase / EAS 相关配置，便于后续 Android 打包继续使用，但这一轮 Expo 调试阶段不再以“Expo 中收到真实远程通知”为交付目标。

如果后续需要继续查看当前 Expo 保留策略和调试约定，请看：

- [docs/expo_debug_setup.md](./docs/expo_debug_setup.md)

## 访问地址

- Django backend: <http://localhost:8000>
- Django health: <http://localhost:8000/api/health/>
- FastAPI model-service: <http://localhost:8010>
- FastAPI docs: <http://localhost:8010/docs>
- MySQL: `localhost:3306`
- Redis: `localhost:6379`

## 常用命令

### Docker

```powershell
docker compose up -d --build
docker compose ps
docker compose logs -f backend
docker compose logs -f model-service
docker compose stop
docker compose down
```

### 移动端

```powershell
npm run start
npm run typecheck
npx expo-doctor
npx eas-cli@latest build -p android --profile preview
```

## Android APK 打包方法

在 `mobile` 目录执行：

```powershell
cd mobile
npx eas-cli@latest build -p android --profile preview
```

打包前请确认：

1. 你的 backend 和 model-service 正在你自己的电脑上运行
2. 手机可以在浏览器中访问你自己电脑的：
   - `http://<your-lan-ip>:8000/api/health/`
3. 如果你不是在最初那台联调机器上打包，请先修改：
   - `mobile/eas.json` 中的 `EXPO_PUBLIC_API_BASE_URL`
   - `mobile/eas.json` 中的 `EXPO_PUBLIC_MODEL_BASE_URL`

可以理解为：

- `mobile/.env` 决定 **Expo 联调时** 连哪台电脑
- `mobile/eas.json` 决定 **EAS 打包出来的 APK** 连哪台电脑

当前项目已经成功产出过多版 APK，说明打包链路已打通。  
如果后续继续修改并重新打包，建议每次同步更新：

- `expo.version`
- `android.versionCode`

## Firebase / FCM / EAS 依赖说明

如果后续继续验证 Android 独立安装包中的提醒功能，需要这几项配置配合存在：

### 已纳入仓库 / 项目配置的部分

- `mobile/google-services.json`
- `mobile/app.json` 中的：
  - `android.package`
  - `android.googleServicesFile`
  - `extra.eas.projectId`
- `mobile/eas.json`

### 已在平台侧配置过的部分

- Expo / EAS 项目
- Android FCM V1 凭证
- Firebase service account

### 说明

- Expo 调试阶段不以推送稳定收件为目标
- Android APK 阶段才能更接近真实推送链路
- 当前我们已经验证：
  - 设备 token 可登记到后端
  - 后端可通过 Expo 通道发起提醒
  - 但设备侧 token 获取偶发超时 / `SERVICE_NOT_AVAILABLE`

如需继续看这部分结论，请看：

- [docs/expo_debug_setup.md](./docs/expo_debug_setup.md)
- [docs/android_packaging_checklist.md](./docs/android_packaging_checklist.md)
- [docs/public_repo_sanitization_checklist.md](./docs/public_repo_sanitization_checklist.md)

## 默认账号

默认 seed 后的管理员账号：

- 用户名：`admin`
- 密码：`MoodFlow@123456`

## 数据与训练

原始数据位于：

- `data/raw/`

处理后的训练数据位于：

- `data/processed/moodflow_emotions.csv`

当前清洗后的实验数据位于：

- `data/processed/clean_v4/`

当前默认保留的模型为：

- `model_service/artifacts/baseline-clean-v4/`

## 补充文档

- [docs/moodflow_backend_summary.md](./docs/moodflow_backend_summary.md)
- [docs/backend_api_test_record.md](./docs/backend_api_test_record.md)
- [docs/expo_debug_setup.md](./docs/expo_debug_setup.md)
- [docs/android_packaging_checklist.md](./docs/android_packaging_checklist.md)
- [TODO.md](./TODO.md)
