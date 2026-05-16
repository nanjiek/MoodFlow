# MoodFlow Mobile

`mobile/` 是仓库内新增的 Expo + TypeScript React Native 客户端，用于实现“可展示、可联调、主要流程可跑通”的双端高保真展示版。

## 技术栈

- Expo
- TypeScript
- Expo Router
- TanStack Query
- AsyncStorage

## 环境变量

在本地启动前配置：

```bash
EXPO_PUBLIC_API_BASE_URL=http://localhost:8000
```

可选：

```bash
EXPO_PUBLIC_MODEL_BASE_URL=http://localhost:8010
```

当前默认不直连模型服务，主要通过 Django backend 提供的接口完成登录、资料、记录、分析、提醒和导出。

## 页面范围

- 认证流：登录、注册、找回密码三步、社交登录占位页
- 主 Tab：首页、记录、成长、我的
- 二级页：记录创建/编辑、分析详情、个人资料、隐私设置、提醒设置、导出设置

## 运行

安装依赖后可执行：

```bash
npm install
npm run start
```
