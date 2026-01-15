import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

# === 1. 代理配置 (如果你在国内直连阿里云，通常不需要代理，可以注释掉) ===
# 如果你的网络环境特殊，仍需代理，请取消注释
# os.environ["http_proxy"] = "http://127.0.0.1:7890"
# os.environ["https_proxy"] = "http://127.0.0.1:7890"

app = Flask(__name__)
CORS(app)  # 允许跨域

# === 2. 配置阿里云 DashScope 客户端 ===
# 请将下面的 sk-xxx 替换为你自己在阿里云百炼控制台获取的 API Key
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")

client = OpenAI(
    api_key=DASHSCOPE_API_KEY, 
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

@app.route('/analyze', methods=['POST'])
def analyze_route():
    data = request.json
    
    # 获取前端参数
    lat = data.get('lat')
    lon = data.get('lon')
    date = data.get('date')
    route_type = data.get('type')  # '进攻' 或 '撤退'
    terrain_hint = data.get('terrain_hint', '')

    print(f"收到请求: {date} {route_type} @ [{lat}, {lon}]")

    # 构建 Prompt
    system_prompt = "你是一位精通1812年拿破仑俄法战争的军事历史学家和地理学家。请基于用户提供的坐标、时间和地形数据进行专业分析。"
    
    user_prompt = f"""
    请分析以下战况：
    1. **时间**: {date}
    2. **坐标**: 经度 {lon:.2f}, 纬度 {lat:.2f} (东欧平原/俄罗斯西部)
    3. **状态**: 法军正在 {route_type}
    4. **地形参考**: {terrain_hint}

    请生成一段简短的分析（200字以内），内容包括：
    - **地理环境**: 该位置附近是否有重要河流（如别列津纳河、第聂伯河）或特殊地形？
    - **军事态势**: 此时法军面临的主要困难是什么？
    - **历史意义**: 这一阶段对战争成败有何影响？

    请用沉稳、专业的历史纪录片旁白口吻回答。
    """

    try:
        # === 3. 调用 API (流式接收但一次性返回) ===
        # 这里使用 deepseek-r1 或 qwen-max
        # 注意：如果你没有开通 DeepSeek，可以将 model 改为 "qwen-max" 或 "qwen-plus"
        completion = client.chat.completions.create(
            model="deepseek-r1",  # 或者 "qwen-max"
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ],
            # 开启思考模式 (仅 DeepSeek R1 系列支持，Qwen 系列请注释掉 extra_body)
            extra_body={"enable_thinking": True},
            stream=True,
            stream_options={"include_usage": True}
        )

        reasoning_content = ""  # 思考过程
        answer_content = ""     # 最终回复

        print("\n--- AI 正在思考 ---")
        
        # 处理流式响应
        for chunk in completion:
            # 过滤掉没有 choices 的 chunk (通常是 usage 信息)
            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta

            # 1. 收集思考过程 (DeepSeek 特有)
            if hasattr(delta, "reasoning_content") and delta.reasoning_content:
                reasoning_content += delta.reasoning_content
                # 在服务器终端打印思考过程，让你看到它在想什么
                print(delta.reasoning_content, end="", flush=True)

            # 2. 收集正式回复
            if hasattr(delta, "content") and delta.content:
                answer_content += delta.content

        print("\n\n--- 回复生成完毕 ---")
        
        # 返回给前端
        # 如果你想把思考过程也展示在网页上，可以把 reasoning_content 也传回去
        # 这里为了保持网页整洁，只返回 final answer
        return jsonify({
            "analysis": answer_content,
            # "reasoning": reasoning_content # 如果前端需要显示思考过程，可以取消注释
        })

    except Exception as e:
        print(f"API 调用错误: {e}")
        return jsonify({"analysis": f"API 调用失败: {str(e)}。请检查 API Key 或 模型名称。"}), 500

if __name__ == '__main__':
    print("🌍 阿里云百炼分析服务已启动: http://localhost:5000")
    app.run(port=5000, debug=True)
    