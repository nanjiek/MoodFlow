# MoodFlow Mobile

`mobile/` 是仓库内新增的 Expo + TypeScript React Native 客户端，用于实现“可展示、可联调、主要流程可跑通”的双端高保真展示版。

## 技术栈

- Expo
- TypeScript
- Expo Router
- TanStack Query
- AsyncStorage

## 环境变量

推荐在 `mobile/.env` 中配置：

```bash
EXPO_PUBLIC_API_BASE_URL=http://<your-lan-ip>:8000
EXPO_PUBLIC_MODEL_BASE_URL=http://<your-lan-ip>:8010
```

说明：

- Android/iOS 真机不能访问你电脑上的 `localhost`
- 如果你不显式配置，Expo 真机调试时会优先尝试根据开发服务器地址自动推断局域网 IP
- Web 模式下仍默认回落到 `http://localhost:8000`

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

如果要在同一局域网真机调试，请确保：

- 手机和电脑连接同一个 Wi-Fi
- backend 暴露在 `0.0.0.0:8000` 或可被局域网访问
- Windows 防火墙已放行对应端口
