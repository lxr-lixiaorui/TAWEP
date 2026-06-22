# AGENTS.md

本文件用于指导在本仓库中工作的 AI 编码代理。请在修改代码前先阅读本文件和 `README.md`。

## 项目概览

这是一个基于 Flask 的 TOEFL Academic Discussion 写作评估应用。

- 入口文件：`app.py`
- 报告生成：`generateReport.py`
- 页面模板：`templates/view.html`
- 静态资源与题库：`static/`
- 题目数据：`static/table/2023_AcaTalk.txt`
- 参考答案：`static/table/2023_AcaTalk_Answer.txt`
- 生成报告目录：`static/table/Record/`

应用会读取题库，展示 Academic Discussion 题目，提交作文后调用 Deepseek 兼容的 OpenAI SDK 接口生成评分和改写建议，并把报告写入 HTML 文件。

## 运行方式

本项目没有锁定依赖文件。开发环境至少需要：

```cmd
pip install flask openai
```

运行前需要设置环境变量：

```cmd
set OPENAI_API_KEY=your_deepseek_api_key
```

在 PowerShell 中可使用：

```powershell
$env:OPENAI_API_KEY="your_deepseek_api_key"
```

启动应用：

```cmd
python app.py
```

当前 `app.py` 使用：

- host: `0.0.0.0`
- port: `1145`
- debug: `True`

访问地址通常为 `http://127.0.0.1:1145`。

## 开发注意事项

- 优先保持现有 Flask 单文件风格，除非用户明确要求重构。
- 修改接口时同步检查 `templates/view.html` 中对应的表单字段、请求路径和返回数据解析。
- `submit_answer` 依赖全局变量 `question`、`nameA`、`nameB`，这些变量由 `/choose_paper` 设置。调整流程时要避免用户未选题就提交导致异常。
- `generateReport.py` 会直接向 `static/table/Record/` 写入 HTML 报告。不要把测试生成的大量报告当作必须提交的源代码变更。
- `static/table/*.txt` 是题库和答案数据，除非任务明确要求，不要改动其内容或编码。
- 仓库中可能存在用户本地生成的报告、缓存和未提交改动。不要还原、删除或覆盖与当前任务无关的文件。
- `__pycache__/` 是运行产物，不应作为功能修改的一部分。

## AI/API 相关约定

- 代码当前使用 `OpenAI(api_key=api_key, base_url="https://api.deepseek.com")`。
- 默认模型为 `deepseek-reasoner`。
- `OPENAI_API_KEY` 实际承载 Deepseek API key；保持 README 和代码说明一致。
- 不要把 API key、示例密钥或用户隐私内容写入仓库。
- 调试前可在作文文本中加入 `debug:True`，应用会返回固定报告，避免消耗 API 调用。
- 作文文本中加入 `AllowOvertime:True` 的行为在前端中处理，修改计时逻辑时需要检查模板脚本。

## 验证建议

小改动后至少执行：

```cmd
python -m py_compile app.py generateReport.py
```

涉及页面或接口时，建议手动验证：

1. 启动 `python app.py`
2. 打开 `http://127.0.0.1:1145`
3. 选择题目并确认
4. 使用包含 `debug:True` 的作文提交
5. 确认页面能展示报告，并且 `static/table/Record/` 下生成 HTML 文件

## 代码风格

- 保持 Python 代码简洁直接。
- 新增注释应解释不明显的业务约束，而不是复述代码。
- 字符串涉及中文提示词、评分规则或页面文本时，注意文件编码使用 UTF-8。
- 对已有提示词和评分输出格式要谨慎修改，因为前端和报告生成依赖 `@@@`、`***` 等分隔符。

