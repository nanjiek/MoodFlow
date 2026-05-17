# MoodFlow PR 提交范围建议

更新时间：2026-05-17

这份文档用于说明：如果后续要向上游仓库提交一个**审核友好**的 PR，哪些内容建议纳入，哪些内容建议暂时排除，以及如何描述这次改动。

## 1. 推荐提交目标

本次更适合整理成一个“上游友好 PR”，重点聚焦以下几个方向：

1. 移动端界面与交互优化
2. Expo / Android APK 联调与打包说明文档
3. 提醒功能在 Expo / APK 环境下的接入与说明
4. 模型默认版本与实验结论文档整理

换句话说，这次 PR 更适合表现为：

- 功能可用性提升
- 移动端体验修整
- 开发与部署文档补强
- 研究 / 实验过程有总结，但不把所有实验产物都塞进 PR

## 2. 建议纳入 PR 的内容

### 2.1 文档

建议纳入：

- `README.md`
- `TODO.md`
- `docs/expo_debug_setup.md`
- `docs/android_packaging_checklist.md`
- `docs/public_repo_sanitization_checklist.md`
- `docs/experiments/emotion_model_experiment_summary.md`

说明：

- `docs/experiments/emotion_model_experiment_summary.md` 可以作为“尝试方案记录”保留在 PR 中
- 这样既能说明我们试过哪些路线，也不会把全部原始产物都塞给审核者

### 2.2 移动端代码

建议纳入：

- 隐私设置交互修复
- 分析结果页退出路径补充
- 个人资料保存反馈
- 成长页折线图与图表留白优化
- 首页 / 登录等文案修整
- Expo / Android 打包相关配置

对应主要目录：

- `mobile/app/`
- `mobile/components/`
- `mobile/constants/`
- `mobile/lib/`
- `mobile/package.json`
- `mobile/package-lock.json`
- `mobile/app.json`
- `mobile/eas.json`
- `mobile/.env.example`
- `mobile/README.md`
- `mobile/assets/branding/`

### 2.3 后端 / 模型服务必要改动

建议纳入：

- 提醒功能接入 Expo Push 的必要后端逻辑
- 默认模型切换到 `baseline-clean-v4` 的必要配置
- 模型服务对实验路线保留的必要说明

对应主要文件：

- `backend/emotions/reminders.py`
- `backend/tests/test_user_reminder_export_api.py`
- `backend/requirements.txt`
- `backend/mlops/management/commands/seed_model_versions.py`
- `docker-compose.yml`
- `model_service/Dockerfile`
- `model_service/README.md`
- `model_service/app/predictor.py`

### 2.4 训练 / 实验脚本

建议纳入：

- `model_service/training/clean_dataset.py`
- `model_service/training/train_linear_svm.py`
- `scripts/interactive_emotion_models.py`
- `scripts/test_backend_endpoints.py`

如果你希望 PR 更偏“工程交付”，也可以只纳入一部分脚本；  
但如果想保留方法论和验证过程，这几份脚本是有价值的。

## 3. 建议暂不纳入 PR 的内容

下面这些内容更适合保留在本地、用于报告、答辩或实验附件，不建议直接塞进上游 PR。

### 3.1 大体积或环境绑定产物

建议暂不提交：

- `model_service/artifacts/baseline-clean-v4/`
- `model_service/artifacts/experiments/`
- `data/processed/clean_v1/`
- `data/processed/clean_v2/`
- `data/processed/clean_v3/`
- `data/processed/clean_v4/`

原因：

- 体积大
- 审核成本高
- 更像实验输出，不像日常维护仓库需要跟踪的源码

### 3.2 本地联调记录 / 截图材料

建议暂不提交：

- `docs/backend_api_test_record.md`
- `docs/backend_api_test_record.json`
- `docs/mobile_ui_screenshots.md`
- `docs/mobile_ui_screenshots/`

原因：

- 适合答辩或汇报材料
- 但对上游仓库来说更像附件而不是核心源码

### 3.3 强环境绑定文件

视情况决定，默认建议谨慎处理：

- `mobile/google-services.json`

说明：

- 如果上游仓库接受将 Firebase Android 配置一起保留，可以提交
- 如果更倾向于“让接手者自行配置 Firebase”，则建议不提交，并在文档中说明如何自行生成

## 4. 当前最推荐的 PR 叙事

建议把这次提交描述成一个组合改进：

### 标题方向

可以考虑类似：

- `Refine mobile UX, Expo/APK workflow, and reminder integration docs`
- `Improve mobile flows and document Expo/APK deployment`

### 内容摘要方向

建议写成三块：

1. **移动端体验优化**
   - 分析结果页退出路径
   - 隐私设置状态同步
   - 关键操作反馈
   - 成长页折线图
   - 文案优化

2. **Expo / Android 打包能力整理**
   - Expo 调试保留
   - Android APK 打包文档补充
   - Firebase / FCM / EAS 配置说明

3. **实验与模型记录整理**
   - 默认模型收口到 `baseline-clean-v4`
   - 分类器 / LLM 路线验证结论
   - 保留实验总结文档，但不提交全部实验产物

## 5. 推荐的实际提交边界

如果希望进一步收缩 PR 大小，我建议最低可行范围如下：

### 必须纳入

- `README.md`
- `TODO.md`
- `docs/expo_debug_setup.md`
- `docs/android_packaging_checklist.md`
- `docs/public_repo_sanitization_checklist.md`
- `docs/pr_submission_scope.md`
- `docs/experiments/emotion_model_experiment_summary.md`
- 相关移动端 UX 改动
- 提醒功能后端关键改动
- `mobile/app.json`
- `mobile/eas.json`

### 可选纳入

- `scripts/interactive_emotion_models.py`
- `scripts/test_backend_endpoints.py`
- `model_service/training/clean_dataset.py`
- `model_service/training/train_linear_svm.py`

### 默认排除

- 截图
- JSON 测试记录
- 清洗后的大数据目录
- 模型 artifacts

## 6. 一句话总结

这次 PR 最适合提交成：

**“移动端体验优化 + Expo / APK 调试与打包文档完善 + 实验路线总结文档”**

而不是：

**“把所有本地产物、截图、实验输出和配置一股脑都推上去”。**
