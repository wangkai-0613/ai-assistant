# 第三方开源软件与模型说明

本项目会携带或下载以下第三方组件。它们分别适用其原始许可证和使用条款，不因放入本项目而改变。

## llama.cpp

- 用途：在 Windows 本机运行 GGUF 模型；项目内置压缩包为 `app/resources/llama-runtime-win-cpu-x64.zip`。
- 上游项目：<https://github.com/ggml-org/llama.cpp>
- 许可证：MIT License。完整许可文本和对应发布信息应随分发的运行时一同保留。替换压缩包时，发布者需重新核对其中附带的依赖与许可文件。

## LLVM OpenMP Runtime

- 用途：内置运行时中的 `libomp.dll`，其完整许可文件已作为 `LICENSE-LLVM-OpenMP` 保存在 ZIP 内。
- 上游项目：<https://github.com/llvm/llvm-project/tree/main/openmp>
- 许可证：Apache License 2.0 with LLVM Exceptions；许可文件还包含适用于部分历史代码的第三方条款。

## Qwen2.5-7B-Instruct-GGUF

- 用途：本地 AI 对话模型；安装时从 ModelScope 下载 `qwen2.5-7b-instruct-q3_k_m.gguf`。
- 模型页：<https://www.modelscope.cn/models/qwen/Qwen2.5-7B-Instruct-GGUF>
- 上游项目：<https://github.com/QwenLM/Qwen2.5>
- 许可证：Apache License 2.0。模型权重不存入 Git 工作树，由用户主动下载；使用和再分发时应遵守模型页公布的当前许可和条款。

## 应用依赖

Python 依赖及版本范围见 `requirements.txt` 和 `requirements-dev.txt`。它们各自适用上游许可证；发布安装包前应使用实际锁定的依赖版本生成并审核完整许可清单。