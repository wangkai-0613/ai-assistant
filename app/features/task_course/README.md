# 任务、课表和提醒模块（1号）

负责任务管理、课表展示和到期/课前提醒。只修改本目录，不触碰 `app/core/`、其他功能模块和主窗口。

## 功能

- 任务增删改查，SQLite 持久化（`~/.xiao_assistant/assistant.db`）
- 任务到期提醒弹窗：完成 / 稍后提醒（5 分钟）
- CSV 课表导入（坏行自动跳过）与一周课表展示
- 明日课程摘要
- 课前 15 分钟提醒（每门课每天只提醒一次）
- 提醒语音播报（遵循设置中的 `voice_enabled`，缺省开启；仅 Windows）

## 启动

先按根目录 [README](../../../README.md) 创建虚拟环境并安装依赖，然后：

```powershell
python -m app.features.task_course.demo
```

## 独立验收链路

1. 启动 demo，课表页应显示自动导入的示例课表（`sample_data/courses.csv`）和明日课程摘要。
2. 点击侧栏"添加一分钟后的测试任务"。
3. 约一分钟后（巡检间隔 30 秒内）收到提醒弹窗，同时语音播报。
4. 点"稍后提醒"会在 5 分钟后再次提醒；点"完成"则任务标记完成。

## 对外接口

- `create_task_page(context)` / `create_course_page(context)`：页面工厂
- `create_services(context)`：注册 `task`、`course`、`reminder` 三个服务并启动巡检
- `TaskService.create()` 接收公共 `TaskDraft`，保存后发出 `context.events.task_created`

## 测试

```powershell
pytest tests/test_task_service.py tests/test_course_service.py tests/test_reminder_service.py
```
