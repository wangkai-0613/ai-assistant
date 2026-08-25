# 小云个人桌面助手（Python MVP）

这是一个面向 Windows 的 PySide6 桌面助手框架。当前提交只提供可运行的应用外壳、公共契约、模块占位页和四组并行开发边界，不包含正式业务实现。

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

程序启动后应能看到首页、任务、课表、AI 助手、天气、系统状态和设置页面。业务未实现时显示占位说明，这是正常状态。

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
```

