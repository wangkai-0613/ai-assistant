# 五人团队并行开发说明

## 团队成员与职责

| 角色 | GitHub 用户名 | 职责 |
|---|---|---|
| 组长 | `wangkai-0613` | 公共契约、模块接线、集成测试和发布 |
| 1号 | `arcadiamuran-web` | 任务、课表和提醒 |
| 2号 | `muzi2887` | AI 和语音输入 |
| 3号 | `Fysync` | 天气、系统状态和设置 |
| 4号 | `nicheng12` | 程序外壳、公共 UI 和资源 |

## 一、合作原则

1. 所有人必须从组长发布的同一个基线提交创建分支。
2. 每人只修改自己的目录，不跨目录顺手改代码。
3. `app/core/` 是冻结区，只有组长可以修改。
4. 模块之间禁止直接导入彼此的内部文件。
5. 每个模块必须能通过自己的 `demo.py` 单独运行。
6. API Key、数据库、录音文件和本地配置不得提交到 GitHub。
7. 功能开发期间不追求复杂动画，先保证最小演示链可用。
8. 每个成员至少提交两个 PR：服务/核心能力一个，页面/交互一个。

## 二、总体工作流

```text
组长发布基线
  -> 四名组员从同一提交建分支
  -> 四名组员分别运行自己的 demo.py 开发
  -> 第一轮 PR：服务和核心能力
  -> 第二轮 PR：页面和交互
  -> 组长在 integration/v0.1 中接线
  -> 全员只修自己模块的缺陷
  -> 组长打包并发布 v0.1.0-demo
```

组员之间不互相等待。依赖尚未实现时使用 Mock 或事件。最终接线由组长负责。

## 三、冻结的跨模块约定

公共类型在 `app/core/contracts.py`：

- `Task`：已保存的任务。
- `TaskDraft`：AI 或表单产生、尚未保存的任务草稿。
- `Course`：一条课程记录，`weekday` 使用 1 至 7 表示周一至周日。
- `WeatherSummary`：天气摘要。
- `SystemSummary`：系统状态摘要。

公共事件在 `app/core/events.py`：

- `task_draft_created(TaskDraft)`：AI 页面确认后发出。
- `task_created(Task)`：任务服务保存后发出。
- `settings_changed()`：设置保存后发出。
- `status_message(str)`：模块希望主程序展示非阻断提示时发出。

禁止这样写：

```python
from app.features.task_course.task_service import TaskService  # AI模块禁止
```

AI模块应该这样做：

```python
context.events.task_draft_created.emit(draft)
```

组长最终负责连接：

```python
context.events.task_draft_created.connect(task_service.create)
```

## 四、统一模块入口

功能模块暴露页面工厂，不允许主窗口了解模块内部类：

```python
def create_page(context):
    return SomePage(context)
```

一个功能包含多个页面时，使用明确名称，例如：

```python
create_task_page(context)
create_course_page(context)
create_settings_page(context)
```

## 五、GitHub规则

- `main` 开启分支保护，禁止直接 push。
- PR 合并前至少由组长检查一次。
- 一个 PR 只解决一个主题，避免超大 PR。
- 提交信息示例：`feat(task): add sqlite task repository`。
- PR 描述必须包含：完成内容、运行命令、手动验收结果、未完成项。
- 不把格式化整个仓库与功能修改放在同一个 PR。
- 出现接口问题先提 Issue，不私下复制另一套模型规避问题。

## 六、两天截止标准

第一天结束前：每人提交核心能力 PR，`demo.py` 可运行。

第二天中午前：每人提交页面 PR，随后冻结新功能。

可砍项：

- 1号：可砍课程主动提醒，保留任务提醒和课表展示。
- 2号：可砍语音输入，保留 AI 文字输入与任务解析。
- 3号：可砍 CPU 实时曲线，保留天气、设置、内存和磁盘。
- 4号：可砍复杂宠物动画，保留主窗口、导航、托盘和统一样式。

任何人不得因为第二优先级未完成而阻塞第一优先级交付。

## 七、完成定义

一个任务只有同时满足以下条件才算完成：

- 代码已推送并发起 PR。
- 独立 demo 可运行。
- 正常流程有手动验收记录。
- 网络、输入或设备失败时不会导致整个程序崩溃。
- 没有提交密钥、数据库或个人路径。
- README 或模块说明中写明启动方法。

