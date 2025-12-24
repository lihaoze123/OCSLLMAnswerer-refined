# OCS AI Answerer Server

一个基于 Python Flask 和 OpenAI 接口（支持 DeepSeek/Qwen 等）的 OCS 网课助手题库服务器。

本项目旨在为 [OCS 网课助手](https://docs.ocsjs.com/) 提供一个本地化的、高智能的 AI 查题后端。它接收 OCS 发送的题目，通过调用大模型（LLM）进行推理，并将答案格式化返回给 OCS 脚本自动答题。

## ✨ 特性

-   **🤖 多模型支持**: 兼容 OpenAI 格式接口，支持 GPT-3.5/4, DeepSeek, Qwen (通义千问) 等模型。
-   **🧠 智能推理**: 专门针对推理模型优化，自动去除 `<think>` 标签，提取核心 JSON 答案。
-   **🎨 炫彩日志**: 控制台实时显示彩色日志，清晰展示题目、选项、AI 推理结果及解析。
-   **🧹 智能清洗**: 自动去除选项中的多余空行和格式杂质，提高 AI 识别准确率。
-   **🧩 多题型适配**: 针对单选、多选、判断、填空题定制不同的 Prompt，大幅提升准确率。


## 🛠️ 安装与运行

## 直接运行

下载Release包，解压后修改`.env`文件中的`OPENAI_API_KEY`和`OPENAI_BASE_URL`，然后运行`OCSAnswererWrapper.exe`即可。

### 1. 克隆或下载本项目
```bash
git clone https://github.com/FengZi-lv/OCSLLMAnswerer.git
cd OCSAnswererWrapper
```

### 2. 安装依赖
建议使用 Python 3.8+ 环境。
```bash
pip install -r requirements.txt
```

### 3. 配置环境变量
复制 `.env.example` 为 `.env` (如果不存在则新建)，并填入您的 API Key：
```ini
# .env 文件内容
OPENAI_API_KEY=sk-您的密钥
# 如果使用第三方代理或本地模型（如 Ollama），请配置 Base URL
# OPENAI_BASE_URL=https://api.deepseek.com/v1
```

### 4. 启动服务器
```bash
python main.py
```
启动成功后，服务器默认运行在 `http://0.0.0.0:5000`。

## 🖥️ OCS 脚本配置

打开 OCS 网课助手的【全局设置】 -> 【题库配置】，点击【新建】，粘贴以下配置：

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
        "handler": "return (res) => res.code === 1 ? [res.question, res.answer, {ai: res.analysis}] : undefined"
    }
]
```
> **注意**: 如果您部署在云服务器上，请将 `localhost` 替换为服务器 IP。



## ⚠️ 免责声明

本项目仅供学习交流使用，请勿用于违反学校规定或法律法规的用途。开发者不对使用本项目产生的任何后果负责。
