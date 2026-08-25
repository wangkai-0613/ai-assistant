# 3号模块：天气、系统状态与设置

负责人：Fysync（GitHub: `Fysync`）
分支：`feature/weather-system-settings`

本模块实现桌面助手的天气查询、系统资源监控和偏好设置三个功能。

## 功能

- **天气**：输入城市名查询实时天气（温度、天气描述、降雨概率），带 30 分钟 TTL 缓存，断网时回退到最近一次缓存结果，不会崩溃。
- **系统状态**：实时显示内存、磁盘和 CPU 占用率。
- **设置**：保存默认城市、OpenRouter API Key（密码框输入，本地 JSON 存储，不写入仓库）、语音提示开关和开机自启（Windows 注册表实现，无需管理员权限）。

配置保存位置：`%USERPROFILE%\.xiao_assistant\settings.json`
天气缓存位置：`%USERPROFILE%\.xiao_assistant\weather_cache.json`

## 启动方法

### 独立运行本模块（演示）

```powershell
cd <项目根目录>
.\.venv\Scripts\Activate.ps1
python -m app.features.weather_system.demo
```

启动后会打开三个标签页：天气 / 系统状态 / 设置。

### 在主程序中接入

组长在主程序初始化时调用：

```python
from app.features.weather_system import (
    create_weather_page,
    create_system_page,
    create_settings_page,
    create_services,
)

services = create_services(context)          # 注册 settings/weather/system/autostart 服务
context.replace_page(4, create_weather_page(context))
context.replace_page(5, create_system_page(context))
context.replace_page(6, create_settings_page(context))
```

页面索引与 `app/shell/main_window.py` 中的 `PAGE_SPECS` 保持一致：天气=4、系统状态=5、设置=6。

## 服务注册表

| 服务名 | 类型 | 说明 |
|---|---|---|
| `settings` | `SettingsService` | 配置读写，`get(key)` / `set(key, value)` |
| `weather` | `WeatherService` | `fetch(city)` 异步查询天气，`get_cached(city)` 读缓存 |
| `system` | `SystemService` | `snapshot()` 返回 `SystemSummary` |
| `autostart` | `AutoStartService` | `is_enabled()` / `set_enabled(bool)` |

## 目录结构

```
weather_system/
├── autostart.py         # 开机自启（Windows 注册表）
├── demo.py              # 独立演示入口
├── pages.py             # 天气/系统状态/设置三个页面
├── services.py          # 服务注册 create_services(context)
├── settings_service.py  # 配置存储服务
├── system_service.py    # 系统状态服务
├── weather_service.py   # 天气查询服务（带缓存）
└── workers.py           # 后台线程（天气查询不阻塞 UI）
```

## 依赖

- `httpx`：天气 HTTP 请求
- `psutil`：系统资源读取
- 均为项目 `requirements.txt` 已有依赖，无需额外安装。