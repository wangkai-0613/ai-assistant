# 小云个人桌面助手（Python MVP）

这是一个面向 Windows 的 PySide6 个人桌面助手 MVP。主程序已集成任务、课表、提醒、AI 对话与任务解析、Windows 本地语音输入、天气、系统状态、设置、开机自启、系统托盘和悬浮入口。

## 环境

- Python 3.11（团队统一版本，不要有人使用 3.13）
- Windows 10/11
- 推荐使用项目内虚拟环境

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python main.py
```

程序启动后可从左侧导航使用首页、任务、课表、AI 助手、天气、系统状态和设置页面。首次运行会在用户目录的 `.xiao_assistant` 中创建本地数据库和配置文件。

AI 功能默认优先使用项目自带的 llama.cpp 本地服务，然后尝试已安装的 Ollama，最后才使用配置的 OpenRouter。均不可用时仍可通过离线规则解析常见中文任务。天气查询需要联网；断网时会尽量显示最近缓存。语音输入需要 Windows SAPI 和 `pywin32`。

## 一键安装本地 AI

在“设置”页的“本地 AI”区域选择保存目录，再点击下载。程序会先从项目内置的 `app/resources/llama-runtime-win-cpu-x64.zip` 安装 llama.cpp；只有该文件缺失时，才会从 GitHub（或 `LLAMA_RUNTIME_URL` 指定的镜像）下载运行时。

模型从 ModelScope 下载 `qwen2.5-7b-instruct-q3_k_m.gguf`，约 3.8GB，支持进度显示、断点续传和 SHA256 校验，建议预留至少 5GB 可用空间。本地服务只监听 `127.0.0.1:11435`。下载中断后重新点击即可续传；校验失败时程序会删除损坏的临时文件。第三方运行时和模型说明见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

## 当前交付范围

- 任务增删、完成、延期提醒与本地持久化
- CSV 明细课表和按周分块 XLSX 课表导入、周课表、明日课程及课前提醒
- AI 文本交互、任务解析确认、可选语音输入
- 天气查询及缓存、CPU/内存/磁盘状态
- 深色/浅色主题、默认城市、OpenRouter Key、语音提示和开机自启设置
- 统一界面、托盘最小化和悬浮入口演示

这是课程/团队项目级 MVP，不包含安装包、云同步、多用户账户或生产级密钥管理。

## 课表文件导入

课表页面支持 `.csv` 和 `.xlsx`。CSV 使用 `weekday,start_time,end_time,name,room` 明细列；XLSX 支持按周分块的教务课表，其中 A 列是“第 N 周”和日期范围，后续列按周一至周日排列，每门课依次包含“节次、课程名称、上课教室”。XLSX 会保存具体上课日期，调课和不同教学周不会互相混淆。

节次时间默认映射为：1–2 节 08:00–09:40、3–4 节 10:00–11:40、5–6 节 14:00–15:40、7–8 节 16:00–17:40、9–12 节 19:00–22:00。

## 团队开发入口

所有成员开始前必须阅读 [TEAM_GUIDE.md](TEAM_GUIDE.md)，并只修改分配给自己的目录。

| 角色 | GitHub 用户名 | 分支 | 负责范围 |
|---|---|---|---|
| 组长 | [`wangkai-0613`](https://github.com/wangkai-0613) | `integration/v0.1` | `app/core/`、应用接线、测试与发布 |
| 1号 | [`arcadiamuran-web`](https://github.com/arcadiamuran-web) | `feature/task-course-reminder` | `app/features/task_course/` |
| 2号 | [`muzi2887`](https://github.com/muzi2887) | `feature/ai-voice` | `app/features/ai_voice/` |
| 3号 | [`Fysync`](https://github.com/Fysync) | `feature/weather-system-settings` | `app/features/weather_system/` |
| 4号 | [`nicheng12`](https://github.com/nicheng12) | `feature/ui-shell` | `app/shell/`、`app/resources/` |

`app/core/` 由组长维护。公共契约如需修改，先提 Issue，由组长统一修改后通知全员更新。

## 验证命令

```powershell
python main.py
python -m app.features.task_course.demo
python -m app.features.ai_voice.demo
python -m app.features.weather_system.demo
python -m app.shell.demo
pytest
ruff check .
python -m compileall -q app main.py
git diff --check
```

