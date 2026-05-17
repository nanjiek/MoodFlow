# MoodFlow PR 文件筛选清单

更新时间：2026-05-17

这份清单是给**实际提交 PR 前**直接使用的。  
默认场景：

- 提交目录使用干净 clone：`MoodFlow-pr`
- 目标是“上游友好 PR”
- 保留尝试过程总结，但不提交所有本地产物

## 1. 推荐纳入 PR 的文件

下面这些内容建议优先纳入。

### 1.1 根目录

- `.env.example`
- `.gitignore`
- `Makefile`
- `README.md`
- `TODO.md`
- `docker-compose.yml`

### 1.2 文档

- `docs/expo_debug_setup.md`
- `docs/android_packaging_checklist.md`
- `docs/public_repo_sanitization_checklist.md`
- `docs/pr_submission_scope.md`
- `docs/pr_file_selection_checklist.md`
- `docs/experiments/emotion_model_experiment_summary.md`

### 1.3 后端 / 模型服务必要改动

- `backend/emotions/reminders.py`
- `backend/tests/test_user_reminder_export_api.py`
- `backend/requirements.txt`
- `backend/mlops/management/commands/seed_model_versions.py`
- `model_service/Dockerfile`
- `model_service/README.md`
- `model_service/app/predictor.py`

### 1.4 移动端代码与配置

- `mobile/.gitignore`
- `mobile/.env.example`
- `mobile/README.md`
- `mobile/app.json`
- `mobile/eas.json`
- `mobile/package.json`
- `mobile/package-lock.json`
- `mobile/expo-env.d.ts`
- `mobile/lib/config.ts`
- `mobile/lib/env.ts`
- `mobile/constants/content.ts`
- `mobile/components/app/brand-hero.tsx`
- `mobile/components/ui/inline-alert.tsx`
- `mobile/app/(app)/(tabs)/growth.tsx`
- `mobile/app/(app)/(tabs)/index.tsx`
- `mobile/app/(app)/(tabs)/records.tsx`
- `mobile/app/(app)/analysis/[id].tsx`
- `mobile/app/(app)/record/[id].tsx`
- `mobile/app/(app)/record/new.tsx`
- `mobile/app/(app)/settings/export.tsx`
- `mobile/app/(app)/settings/privacy.tsx`
- `mobile/app/(app)/settings/profile.tsx`
- `mobile/app/(app)/settings/reminders.tsx`
- `mobile/app/(auth)/forgot/verify-code.tsx`
- `mobile/app/(auth)/login.tsx`
- `mobile/app/(auth)/register.tsx`
- `mobile/app/(auth)/social.tsx`
- `mobile/app/+not-found.tsx`

### 1.5 移动端品牌资源

- `mobile/assets/branding/README.md`
- `mobile/assets/branding/icon.png`
- `mobile/assets/branding/adaptive-icon.png`
- `mobile/assets/branding/splash.png`

### 1.6 脚本 / 训练辅助

- `scripts/test_backend_endpoints.py`
- `scripts/interactive_emotion_models.py`
- `model_service/training/clean_dataset.py`
- `model_service/training/train_linear_svm.py`

## 2. 默认建议排除的文件

下面这些默认不建议进上游 PR。

### 2.1 大体积数据 / 产物

- `data/processed/clean_v1/`
- `data/processed/clean_v2/`
- `data/processed/clean_v3/`
- `data/processed/clean_v4/`
- `model_service/artifacts/baseline-clean-v4/`
- `model_service/artifacts/experiments/`

### 2.2 截图与汇报附件

- `docs/mobile_ui_screenshots.md`
- `docs/mobile_ui_screenshots/`
- `docs/backend_api_test_record.md`
- `docs/backend_api_test_record.json`

### 2.3 纯实验脚本目录（如不想让 PR 过大）

以下可以视情况排除：

- `scripts/experiments/`
- `docs/experiments/` 下除 `emotion_model_experiment_summary.md` 之外的内容

### 2.4 环境绑定文件（需看仓库策略）

默认建议谨慎处理：

- `mobile/google-services.json`
- `mobile/.npmrc`

说明：

- `mobile/google-services.json` 是否纳入，取决于你是否希望把 Firebase Android 配置一起交给仓库
- `mobile/.npmrc` 更像本机 npm 兼容修补，一般不建议进上游 PR，除非上游同样存在这个问题

## 3. 建议二次确认再决定的文件

下面这些文件不一定有问题，但建议在正式 `git add` 前再看一眼：

- `mobile/google-services.json`
- `mobile/eas.json`
- `mobile/app.json`

确认点：

1. 是否允许保留当前 Expo / EAS 绑定信息
2. 是否允许保留当前局域网打包环境变量
3. 是否需要把说明保留在文档里，但源码里不提交这些绑定配置

## 4. 推荐的实际操作顺序

在干净 clone（例如 `MoodFlow-pr`）里操作：

### 第一步：先查看状态

```powershell
git status --short
```

### 第二步：优先按文件手动 `git add`

也就是优先添加“推荐纳入 PR”的文件，而不是直接：

```powershell
git add .
```

### 第三步：再次检查暂存内容

```powershell
git diff --cached --stat
git diff --cached
```

### 第四步：确认未混入以下内容

- 大体积数据目录
- 本地截图附件
- SQLite 数据库
- 本地缓存
- 不必要的 Firebase 私有材料

## 5. 推荐的最小可交付 PR

如果你希望 PR 尽可能小而清晰，最小建议版本可以只包含：

- 核心移动端 UX 改动
- `README.md`
- Expo / APK 相关说明文档
- `docs/experiments/emotion_model_experiment_summary.md`
- 提醒后端关键接入改动

这样审核者会更容易抓住重点。

## 6. 一句话总结

这次最稳的提交方式不是“把当前目录全部推上去”，而是：

**保留代码改动、保留必要文档、保留实验总结，但把大产物、截图、清洗数据和本地附件先挡在 PR 外。**
