# MoodFlow Expo 调试与当前交付说明

更新时间：2026-05-17

## 1. 当前项目状态

当前仓库已经整理为一套可本地联调、可真机预览、便于后续继续打包的结构：

- 后端：Django + MySQL + Redis
- 模型服务：FastAPI
- 移动端：Expo + TypeScript + Expo Router
- 当前保留的主模型：`baseline-clean-v4`

移动端目前主要目标是：

- 在 Expo 中完成界面调试与主流程联调
- 保留后续 Android 打包所需配置
- 不再把“Expo Go 中验证远程消息推送”作为当前阶段目标

## 2. 当前保留的关键决定

### 2.1 情绪分析主模型

当前默认保留：

- `model_service/artifacts/baseline-clean-v4/`

这是目前选择保留的主模型版本，用于后端和移动端联调。

### 2.2 Expo 版本

移动端当前已回退并固定在：

- **Expo SDK 52**

这样做的原因是：

- 便于继续沿用当前 Expo 调试流
- 避免继续在 SDK 53/54 的 Expo Go 限制上消耗精力

### 2.3 消息推送策略

当前仓库中保留了部分推送相关配置（如 `google-services.json`、EAS/Firebase 配置），是为了后续 Android 打包时继续使用。

但在**当前 Expo 预览阶段**，我们明确采用以下约束：

- 不把 Expo Go 作为远程推送验证环境
- 不再以“Expo 里必须收到手机通知”为当前交付目标
- 提醒设置页面保留，用于界面和接口流程调试

也就是说：

- **提醒设置功能保留**
- **Expo 预览中的真实远程推送暂不作为交付要求**

## 3. 当前移动端已完成的前端修整

本轮已经完成以下移动端优化：

### 3.1 分析结果页

- 增加“查看记录列表”
- 增加“完成并返回首页”
- 提交纠正后增加成功/失败反馈

### 3.2 成长页

- 将成长曲线从纯文本列表改为轻量折线图
- 为折线图增加上下留白，避免点位贴边
- 继续保留文字摘要，方便阅读

### 3.3 关键操作反馈

- 个人资料保存增加成功/失败提示
- 分析纠正增加成功/失败提示
- 隐私设置失败时提供错误提示

### 3.4 隐私设置

- 修复开关切换后状态闪回问题
- 使用本地状态与乐观更新保持界面稳定
- 去除“隐私设置已更新”成功提示，避免页面布局抖动
- 修复两个开关互相影响颜色的问题

## 4. Expo 调试运行方式

### 4.1 后端服务

在项目根目录执行：

```powershell
cd MoodFlow-main
docker compose up -d --build
```

健康检查地址：

- Backend: <http://localhost:8000/api/health/>
- Model Service: <http://localhost:8010/health>

### 4.2 移动端 Expo 调试

在 `mobile` 目录执行：

```powershell
cd mobile
npm install
npm run start
```

建议准备 `mobile/.env`：

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

- 这里的 `.env` 主要服务于本地 Expo 联调
- 它适合你本机开发阶段反复修改
- 它**不适合作为 EAS 远程构建的唯一依赖**

### 4.3 真机调试要求

- 手机和电脑连接同一 Wi-Fi
- Windows 防火墙允许 Expo 和后端端口访问
- 当前推荐继续使用 Expo 进行界面与主流程调试
- 如遇到局域网不通，请优先检查手机/电脑 VPN、路由器 AP 隔离、防火墙端口放行

## 5. 当前已做过的关键工程处理

这一轮为了保留 Expo 并兼顾后续 APK 打包，已经完成这些工作：

### 5.1 保留主模型

- 当前默认保留 `baseline-clean-v4`

### 5.2 固定 Expo 与 EAS 配置

- `mobile/app.json` 已补齐：
  - `icon`
  - `splash`
  - `android.adaptiveIcon`
  - `android.versionCode`
- `mobile/eas.json` 已补齐：
  - `preview` 构建环境变量
  - `EXPO_PUBLIC_API_BASE_URL`
  - `EXPO_PUBLIC_MODEL_BASE_URL`

### 5.3 调整 Android 明文网络配置

当前项目为了访问本机局域网后端，已通过 `expo-build-properties` 插件为 Android 构建补充：

- `usesCleartextTraffic = true`

这一步是为了让独立 Android 安装包可以访问：

- `http://192.168.x.x:8000`

## 6. 当前不纳入 Expo 调试目标的事项

以下内容当前**不作为 Expo 预览阶段的完成标准**：

- Expo Go 中真实远程推送收件验证
- 完整 Android 推送闭环
- 最终商店发布级推送验证

原因很简单：

- 这些能力更适合放到后续 Android 独立安装包/打包阶段完成
- 当前阶段继续强行在 Expo Go 中验证，会带来额外环境噪声

## 7. 提醒功能当前结论

当前提醒相关结论如下：

- 后端提醒链路可工作
- 设备 token 曾成功登记到后端
- 后端存在 `sent / expo` 的成功提醒记录
- 但客户端在获取 Expo Push Token 时偶发：
  - 请求超时
  - `SERVICE_NOT_AVAILABLE`
  - `IOException`

这说明：

- 问题不主要在 Django 后端
- 更像是 Android 设备侧获取 Expo / FCM token 时存在瞬时不稳定

因此当前阶段建议：

- 保留提醒设置页和接口
- 保留 Firebase / EAS / FCM 配置
- 不把“Expo 中稳定收到真实推送”作为当前交付目标

## 8. 后续推荐顺序

当前更推荐的后续节奏：

1. 继续用 Expo 调试 UI、交互和主流程
2. 完成剩余前端体验优化
3. 确认后端与模型服务稳定
4. 再进入 Android 打包与真机验证

## 9. 相关文档

可以配合以下文档一起看：

- [README.md](../README.md)
- [TODO.md](../TODO.md)
- [moodflow_backend_summary.md](./moodflow_backend_summary.md)
- [backend_api_test_record.md](./backend_api_test_record.md)
- [android_packaging_checklist.md](./android_packaging_checklist.md)
