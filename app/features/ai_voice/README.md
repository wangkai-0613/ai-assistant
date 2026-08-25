# 2号模块：AI 和语音输入

对外只暴露 `create_page(context)`，其余文件均为内部实现，其他模块不应直接导入。

## 运行方式

```powershell
python -m app.features.ai_voice.demo
```

输入“明天下午三点提醒我交报告”，回车或点“发送”，在确认对话框中点“OK”，
终端会打印假接收器收到的 `TaskDraft`。不需要联网、不需要配置任何 Key 也能跑通，
因为三级后端里最后一级是离线规则解析。

## AI 后端：本地优先

调用顺序由 `AI_BACKEND_ORDER` 控制，默认 `ollama,openrouter`：

1. **本地 Ollama**（优先）：在本机安装 [Ollama](https://ollama.com) 并执行

   ```powershell
   ollama serve
   ollama pull qwen2.5:7b-instruct
   ```

   默认地址 `http://127.0.0.1:11434`，模型名 `qwen2.5:7b-instruct`，可在 `.env` 中通过
   `OLLAMA_HOST` / `OLLAMA_MODEL` 覆盖。

2. **云端 OpenRouter**（本地不可用时兜底）：在仓库根目录 `.env` 中配置
   `OPENROUTER_API_KEY` 和 `OPENROUTER_MODEL`。

3. **离线规则解析**（前两级都失败/未配置时的最终兜底）：用正则识别中文时间
   （今天/明天/后天 + 几点几分/半/一刻）和常见触发词（提醒我/记得/别忘了等），
   保证核心演示链路不依赖任何外部服务。

无论走到哪一级，用户看到的都是同一个确认对话框；状态栏（`status_message`
事件）会提示当前使用的是本地模型、云端模型还是离线规则。

## 语音输入（第二优先级，可砍）

点击“🎙 录音”开始，再次点击“⏹ 停止录音”结束，识别结果会追加到输入框。
使用 Windows 自带 SAPI（`pywin32`），全程本地、不联网。未安装 `pywin32`
或不在 Windows 上运行时，麦克风按钮会自动禁用并给出提示，不影响文字对话。

```powershell
python -m pip install pywin32
```

## 契约边界

- 不导入 `app.features.task_course` 或任何其他模块内部代码。
- 不直接写数据库。
- 用户确认任务后只调用 `context.events.task_draft_created.emit(draft)`。
- 网络失败、超时、未配置 Key、麦克风不可用都只会在界面上提示，不会让程序崩溃。
