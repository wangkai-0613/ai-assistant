# 2号（muzi2887）：AI 和语音输入

只修改本目录。不得导入任务模块内部代码，也不得直接写数据库。

## 第一优先级

- OpenRouter文字对话。
- 把自然语言解析成公共 `TaskDraft`。
- 任务确认对话框。
- API超时、无密钥和网络失败提示。

## 第二优先级

- 点击开始/停止录音。
- 录音转文字并填回输入框。

## 必须暴露

```python
create_page(context)
```

用户确认任务后只执行：

```python
context.events.task_draft_created.emit(draft)
```

不要调用任务页面，不要导入 `app.features.task_course`。

## 独立验收

运行 `python -m app.features.ai_voice.demo`，输入“明天下午三点提醒我交报告”，确认后由假接收器打印 `TaskDraft`。

