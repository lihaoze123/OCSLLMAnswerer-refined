# OCS AI Answerer Server

一个本地 OCS 网课助手 AI 题库服务。服务接收 OCS 发送的题目，通过兼容 OpenAI
Chat Completions 的大模型接口生成答案，并按 OCS 题库协议返回结果。

## 特性

- FastAPI 本地 API 服务，保留 `/` 和 `/search` 兼容接口。
- 通过 LiteLLM 调用主流 OpenAI-compatible provider。
- 自动识别题目和选项中的图片 URL，并把图片传给支持视觉输入的模型。
- 支持 `LLM_*` 新配置，并兼容旧的 `OPENAI_*` 配置。
- 自动清理 `<think>`、Markdown fence 和包裹文本，再用 Pydantic 校验答案 JSON。
- 通过 `logging + RichHandler` 保留清晰的终端请求、答案、解析日志。
- 使用 `uv`、`ruff`、`ty`、`pytest` 作为开发工具链。

## 安装

本项目需要 Python 3.13。

```bash
uv sync
```

复制环境变量样例：

```bash
cp .env.example .env
```

然后编辑 `.env`：

```env
LLM_API_KEY=your_api_key_here
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=openai/gpt-4o-mini
LLM_TIMEOUT=30
LLM_JSON_MODE=auto
```

`LLM_MODEL` 必填，没有硬编码默认模型。旧配置 `OPENAI_API_KEY`、`OPENAI_BASE_URL`
和 `OPENAI_MODEL` 仍会作为兼容回退。

如果题目包含图片 URL，请配置支持视觉输入的模型；服务会把图片 URL 作为多模态
`image_url` 内容传给 LiteLLM，但不会下载、缓存或 OCR 图片。

`LLM_JSON_MODE` 可选值：

- `auto`：默认值。LiteLLM 判断 provider 支持 `response_format` 时启用 JSON mode。
- `on`：强制传入 `response_format={"type":"json_object"}`。
- `off`：不传 `response_format`。

## 运行

推荐入口：

```bash
uv run python main.py
```

也可以直接使用 ASGI server：

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 5000
```

服务默认运行在 `http://0.0.0.0:5000`。

## OCS 脚本配置

打开 OCS 网课助手的【全局设置】 -> 【题库配置】，点击【新建】，粘贴：

```json
[
    {
        "name": "AI题库",
        "homepage": "http://localhost:5000",
        "url": "http://localhost:5000/search",
        "method": "post",
        "type": "GM_xmlhttpRequest",
        "contentType": "json",
        "data": {
            "title": "${title}",
            "options": "${options}",
            "type": "${type}"
        },
        "handler": "return (res) => { if (res.code === 1) { let answer = String(res.answer ?? '').trim(); if (answer === '正确') answer = '对'; if (answer === '错误') answer = '错'; return [res.question, answer, {ai: res.analysis}]; } return undefined; }"
    }
]
```

如果部署在其他机器上，请把 `localhost` 替换为服务器地址。

## 开发命令

```bash
uv run ruff format
uv run ruff check
uv run ty check
uv run pytest
```

测试默认不访问真实模型，也不需要 API key。

## 免责声明

本项目仅供学习交流使用，请勿用于违反学校规定或法律法规的用途。开发者不对使用本项目产生的任何后果负责。
