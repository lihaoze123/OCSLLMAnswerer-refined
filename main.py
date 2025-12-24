import os
import json
import re
from datetime import datetime
from flask import Flask, request, jsonify
from openai import OpenAI
from dotenv import load_dotenv
from colorama import init, Fore, Style

# 初始化 colorama
init(autoreset=True)

# 加载环境变量
load_dotenv()

app = Flask(__name__)

# 配置 OpenAI 客户端
api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL")

if not api_key:
    print(Fore.RED + "Warning: OPENAI_API_KEY is not set in environment variables.")

client = OpenAI(
    api_key=api_key,
    base_url=base_url if base_url else None
)

def log_info(msg):
    print(f"{Fore.CYAN}[INFO] {datetime.now().strftime('%H:%M:%S')} {Style.RESET_ALL}{msg}")

def log_success(msg):
    print(f"{Fore.GREEN}[SUCCESS] {datetime.now().strftime('%H:%M:%S')} {Style.RESET_ALL}{msg}")

def log_error(msg):
    print(f"{Fore.RED}[ERROR] {datetime.now().strftime('%H:%M:%S')} {Style.RESET_ALL}{msg}")

def log_request(title, options, q_type):
    print(f"\n{Fore.YELLOW}新的请求 [{datetime.now().strftime('%H:%M:%S')}] {Style.RESET_ALL}")
    print(f"{Fore.BLUE}题目:{Style.RESET_ALL} {title}")
    print(f"{Fore.BLUE}类型:{Style.RESET_ALL} {q_type}")
    if options:
        print(f"{Fore.BLUE}选项:{Style.RESET_ALL} \n{options.strip()}")

def log_response(answer, analysis):
    print(f"{Fore.MAGENTA}答案:{Style.RESET_ALL} {answer}")
    print(f"{Fore.MAGENTA}解析:{Style.RESET_ALL} {analysis}")

# 题型映射
TYPE_MAPPING = {
    "single": "单选题",
    "multiple": "多选题",
    "judgement": "判断题",
    "completion": "填空题",
    "unknown": "未知类型"
}

def get_chatgpt_answer(title, options, original_type):
    """
    调用 ChatGPT 获取答案
    """
    # 转换题型为中文
    question_type = TYPE_MAPPING.get(original_type, original_type)
    
    # 根据题型生成特定指令
    special_instruction = ""
    if original_type == "multiple":
        special_instruction = "重要提示：这是一道【多选题】，请务必仔细分析所有选项，选出所有正确的答案，并严格用 '#' 号分隔（例如：A#C#D）。不要漏选！"
    elif original_type == "completion":
        special_instruction = "重要提示：这是一道【填空题】，请直接输出最准确的填空内容，不要输出选项字母。"
    elif original_type == "judgement":
        special_instruction = "重要提示：这是一道【判断题】，请根据选项回答正确或错误。"

    # 简单的 Prompt，不做过多修饰，保持核心逻辑
    prompt = f"""
你是一个专业的学术助教。请仔细阅读题目和选项，选出最正确的答案。

题目: {title}
选项: {options}
题目类型: {question_type}
{special_instruction}

请严格遵守以下规则：
1. 仅输出一个合法的 JSON 对象。
2. 不要包含 Markdown 标记。
3. JSON 格式必须如下：
{{
    "answer": "这里填最准确的一个选项内容。如果是多选，用#号分隔",
    "analysis": "这里填写简短的解析"
}}
"""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一个只输出 JSON 的专业做题助手。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
        )
        content = response.choices[0].message.content.strip()

        # 清洗逻辑
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
        if content.startswith("```json"): content = content[7:]
        if content.endswith("```"): content = content[:-3]
        content = content.strip()

        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
             content = match.group(0)
             
        result = json.loads(content)
        return result
    except Exception as e:
        log_error(f"OpenAI 调用或解析失败: {e}")
        return {"answer": "未知", "analysis": "服务器处理出错"}

@app.route('/', methods=['GET', 'HEAD'])
def index():
    return jsonify({"code": 1, "msg": "OCS ChatGPT Server is running"}), 200

@app.route('/search', methods=['POST'])
def search_answer():
    try:
        data = request.get_json(force=True, silent=True)
        if data is None:
            try:
                data = json.loads(request.data)
            except Exception:
                return jsonify({"code": 0, "msg": "无法解析 JSON 数据"}), 400

        title = data.get('title', '')
        options = data.get('options', '')
        q_type = data.get('type', 'Unknown')

        if options:
            # 清理选项：去除每一行的前后空格，并过滤掉空行，重新组合
            options = "\n".join([line.strip() for line in options.split('\n') if line.strip()])

        if not title:
            return jsonify({"code": 0, "msg": "题目为空"}), 400

        # 获取中文题型名称用于日志显示
        display_type = TYPE_MAPPING.get(q_type, q_type)
        log_request(title, options, display_type)

        result = get_chatgpt_answer(title, options, q_type)
        
        answer = result.get("answer", "未知")
        analysis = result.get("analysis", "无解析")
        
        log_response(answer, analysis)

        return jsonify({
            "code": 1,
            "question": title,
            "answer": answer,
            "analysis": analysis
        })

    except Exception as e:
        log_error(f"服务器内部错误: {e}")
        return jsonify({"code": 0, "msg": str(e)}), 500

if __name__ == '__main__':
    log_info(f"服务启动在 http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
