# OCS AI Answerer Server

一个本地 OCS 网课助手 AI 题库服务。服务接收 OCS 发送的题目，通过 Pydantic AI
调用 OpenAI-compatible 大模型接口生成答案，并按 OCS 题库协议返回结果。

## 特性

- FastAPI 本地 API 服务，保留 `/` 和 `/search` 兼容接口。
- 通过 Pydantic AI 调用 OpenAI-compatible provider，并用 Pydantic 结构化校验答案。
- 自动识别题目和选项中的图片 URL，本地下载图片后传给视觉模型。
- 文本模型和视觉模型分开配置，图片题缺少视觉模型时返回兜底答案。
- 图片下载参考 ZError 的多请求头策略，支持超星、智慧树等教育平台 Referer。
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
AI_PROVIDER=openai-compatible
AI_API_KEY=your_api_key_here
AI_BASE_URL=https://api.openai.com/v1
AI_TEXT_MODEL=gpt-4o-mini
AI_VISION_MODEL=gpt-4o
AI_TIMEOUT=30
AI_TEMPERATURE=0.3
CHAOXING_COOKIE=
```

`AI_TEXT_MODEL` 用于普通文本题，`AI_VISION_MODEL` 用于包含图片 URL 的题目。没有硬编码默认模型。
本版本不再兼容旧的 `LLM_*` / `OPENAI_*` 配置。

如果题目包含图片 URL，请配置支持视觉输入的 `AI_VISION_MODEL`。服务会在本地下载图片，
校验图片类型和大小，再通过 Pydantic AI 的二进制图片输入传给模型。任意图片下载失败时，
服务会返回兜底答案，不会跳过图片继续猜测。超星图片如需登录态，可把浏览器里已登录超星的
Cookie 填到 `CHAOXING_COOKIE`；该 Cookie 只用于本地下载超星图片。图片不会持久化缓存。

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
