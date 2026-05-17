# MoodFlow Android 打包与依赖说明

更新时间：2026-05-17

## 结论摘要

当前项目已经**基本具备进入 Android 打包验证流程的条件**。

从“能不能开始打包”这个角度看，核心前置项大多已经齐了；从“打出来的包是否足够像一个正式可交付版本”这个角度看，还建议补几项品牌与体验配置。

## 一、已完成的前置项

以下项目已经完成，当前不构成 Android 打包阻塞：

### 1. Expo / EAS 基础配置

- [x] `mobile/app.json` 已存在
- [x] `mobile/eas.json` 已存在
- [x] Expo 项目已绑定 `projectId`
- [x] `owner` 已配置
- [x] Android 包名已配置：`com.moodflow.mobile`

### 2. Firebase / Android 推送基础配置

- [x] `mobile/google-services.json` 已接入
- [x] `app.json` 已配置 `android.googleServicesFile`
- [x] Firebase service account 已准备
- [x] EAS 中已配置 FCM V1 凭证
- [x] Expo / EAS 项目已绑定 `projectId`
- [x] `preview` 构建环境变量已写入 `mobile/eas.json`

说明：

- 这表示后续如果改走独立 Android 安装包路线，推送能力有继续验证的基础。
- 但当前 Expo 预览阶段不以“真实消息推送在 Expo 中可用”为目标。

### 3. 代码健康度

- [x] `npm run typecheck` 通过
- [x] `npx expo-doctor` 通过（17/17）
- [x] 当前移动端主要交互问题已完成一轮修整

### 4. 当前调试环境

- [x] 项目已固定在 Expo SDK 52
- [x] `mobile/.env` 调试方式明确
- [x] 局域网联调方式已经可用
- [x] Android 明文访问本机局域网后端的配置已补齐

## 二、Android APK 实际打包方式

在 `mobile` 目录执行：

```powershell
cd mobile
npx eas-cli@latest build -p android --profile preview
```

### 当前已验证

项目已经成功构建出多版 Android `preview` APK，说明：

- EAS 构建链路可用
- Android 包名配置可用
- 图标 / 启动图 / adaptive icon 配置可用
- Firebase / `google-services.json` 没有阻塞构建

### 当前打包约定

后续每次重新打包时，建议同步更新：

- `expo.version`
- `android.versionCode`

这样可以清楚区分手机里安装的是不是最新包。

## 三、当前仍建议补充的事项

以下项目**不一定阻塞内部打包验证**，但会影响成品感、后续迭代成本或发布质量。

### 1. App 图标与启动图

当前 `app.json` 中已经补齐配置，但后续仍建议逐步替换为最终品牌资源。

影响：

- 打包已经可用
- 但后续仍建议根据最终展示需求继续优化品牌资产

建议：

- 若当前仍为过渡版视觉，后续再换成最终图标与启动图

### 2. Android 版本号管理

当前已配置并开始使用：

- `version`
- `android.versionCode`

建议：

- 后续每次重新打包都继续递增
- 保持版本名与版本号同步可追踪

### 3. 应用展示信息还比较基础

当前配置里较基础的字段已经有：

- `name`
- `slug`
- `scheme`

但后续如果要进一步靠近正式安装包，建议逐步补：

- 更正式的品牌图标
- 更明确的版本策略
- 必要时补充权限说明文案

### 4. 推送功能在打包后仍需单独验证

虽然当前 Firebase/EAS 已基本接上，但真正是否可用仍要放到**独立 Android 包**里再验证。

这不是当前的配置缺失，而是：

- Expo Go 与独立 Android 包的运行环境不同
- 最终推送验证必须以后者为准
- 当前后端已有成功的 Expo 分发记录，但客户端 token 获取偶发不稳定

## 四、FCM / Firebase / EAS 依赖说明

当前 Android 提醒相关依赖链如下：

### 1. 仓库内文件

- `mobile/google-services.json`
- `mobile/app.json`
- `mobile/eas.json`

### 2. Expo / EAS 项目侧

- Expo 账号登录
- EAS 项目关联
- `projectId`

### 3. Firebase 平台侧

- Firebase Android 应用
- Android 包名：`com.moodflow.mobile`
- FCM V1 service account

### 4. 已知现象

当前链路里已经出现过：

- 设备 token 成功登记
- 后端 `sent / expo` 成功记录

也出现过：

- `SERVICE_NOT_AVAILABLE`
- `IOException`
- 获取 token 超时

因此当前判断是：

- 后端链路已打通
- 客户端获取推送 token 偶发存在不稳定

## 五、当前判断：哪些是“硬前置”，哪些是“建议项”

### 已具备，可以开始打包

如果你的目标是：

- 打一个内部预览包
- 安装到 Android 真机上继续测主流程

那么现在已经可以开始。

### 建议先补，再打包更舒服

如果你的目标是：

- 打出来的包更像一个完整产品
- 减少后续返工

那建议先补：

1. App 图标
2. 启动图
3. `android.versionCode`

## 六、推荐的下一步

### 路线 A：直接开始内部打包验证

适合现在就想尽快看 Android 安装包效果。

建议顺序：

1. 保持当前代码不再大改
2. 执行 EAS Android `preview` 构建
3. 真机安装
4. 继续验证登录、记录、分析、成长、设置等主流程

### 路线 B：先补品牌资源，再打包

适合希望第一版安装包就更完整。

建议先补：

1. App 图标
2. 自适应图标
3. 启动图
4. `android.versionCode`

## 七、当前建议

结合你现在的项目阶段，我的建议是：

**如果你现在主要是做功能验证和真机联调，可以直接进入 Android 打包；如果你希望这次包更像“可展示版本”，建议先补图标、启动图和 `versionCode`。**

## 八、官方文档参考

- Expo EAS Build（Android 构建）：
  - https://docs.expo.dev/build/introduction/
- Expo Push Notifications：
  - https://docs.expo.dev/push-notifications/push-notifications-setup/
- Firebase Android 接入：
  - https://firebase.google.com/docs/android/setup
