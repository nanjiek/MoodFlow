# Branding Placeholders

当前目录中的文件为 Android 打包前的占位资源：

- `icon.png`
- `adaptive-icon.png`
- `splash.png`

它们的作用是：

- 让 `app.json` 中的图标、启动图和自适应图标配置保持可用
- 避免后续打包时因为资源路径缺失而失败

后续如需替换为正式设计稿，请直接覆盖同名文件即可。
