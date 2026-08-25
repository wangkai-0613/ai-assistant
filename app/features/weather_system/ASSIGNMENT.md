# 3号（Fysync）：天气、系统状态和设置

只修改本目录。设置使用独立 JSON，不与任务模块争用 SQLite。

## 第一优先级

- 城市、OpenRouter Key和语音开关的保存与读取。
- 手动城市天气查询。
- 内存和磁盘状态。
- 断网或权限失败时显示错误且不崩溃。

## 第二优先级

- CPU占用。
- 开机自启。
- 天气缓存和首页摘要。

## 必须暴露

```python
create_weather_page(context)
create_system_page(context)
create_settings_page(context)
create_services(context)
```

API Key不得打印、写入仓库或硬编码。配置变化后发出 `context.events.settings_changed`。

## 独立验收

运行 `python -m app.features.weather_system.demo`，设置城市并查询天气，显示内存和磁盘，重启后配置仍保留。

