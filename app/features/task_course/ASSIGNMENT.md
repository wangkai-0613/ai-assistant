# 1号（arcadiamuran-web）：任务、课表和提醒

只修改本目录。不要修改 `app/core/`、AI模块、天气模块和主窗口。

## 第一优先级

- SQLite任务增删改查。
- 任务列表页面。
- 到期检查、提醒弹窗、完成和稍后提醒。
- CSV课表导入和一周课表展示。

## 第二优先级

- 明日课程摘要。
- 课程开始前提醒。
- 语音播报提醒。

## 必须暴露

```python
create_task_page(context)
create_course_page(context)
create_services(context)
```

`TaskService.create()` 接受公共 `TaskDraft`，成功后发出 `context.events.task_created`。不得自建另一套公共 Task 类型。

## 独立验收

运行 `python -m app.features.task_course.demo`，完成：导入CSV、添加一分钟后任务、收到提醒、标记完成。

