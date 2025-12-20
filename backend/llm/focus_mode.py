# backend/llm/focus_mode.py
import requests
import markdown
import json
from backend.config import (
    DEEPSEEK_API_KEY, 
    DEEPSEEK_API_URL, 
    DEEPSEEK_REASONER_MODEL,
    NAHIDA_PROMPT
)

def get_nahida_response(user_input: str) -> dict:
    """
    纳西妲专属处理函数 (无状态 + 深度思考)
    """
    # 1. 构造请求头
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }
    
    # 2. 构造消息
    # 注意：这里不传入 _chat_history，纳西妲每次都基于全新的视角思考
    messages = [
        {"role": "system", "content": NAHIDA_PROMPT},
        {"role": "user", "content": user_input}
    ]
    
    # 3. 构造 Payload，切换到推理模型
    payload = {
        "model": DEEPSEEK_REASONER_MODEL,
        "messages": messages,
        "stream": False, 
        "max_tokens": 4096, # 深度思考需要更多字数
        "temperature": 0.8  # 稍微有一点点灵动
    }
    
    try:
        print(f"🌱 [纳西妲] 正在链接虚空终端进行思考... (Model: {DEEPSEEK_REASONER_MODEL})")
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=90) # 推理模型较慢，超时设长点
        
        # 调试：打印一下看看是否出错
        if response.status_code != 200:
            print(f"API Error: {response.text}")
            
        response.raise_for_status()
        data = response.json()
        
        if "choices" in data and len(data["choices"]) > 0:
            message_obj = data["choices"][0]["message"]
            
            # 4. 关键点：提取思维链 (Reasoning Content)
            # DeepSeek R1 会把思考过程放在 reasoning_content 字段，把结果放在 content 字段
            reasoning_text = message_obj.get("reasoning_content", "")
            final_content = message_obj.get("content", "")
            
            # 如果用的是普通模型兼容，reasoning_text 可能为空，我们做个处理
            if not reasoning_text:
                reasoning_text = "（纳西妲正在整理虚空中的知识...）"
            
            # 5. 格式化为前端可展示的 HTML
            html_output = _format_nahida_html(reasoning_text, final_content)
            
            return {
                "raw": final_content,
                "html": html_output,
                "mode": "focus"
            }
        else:
            raise ValueError("API响应格式异常")

    except Exception as e:
        error_msg = f"哎呀，虚空终端连接好像断开了... ({str(e)})"
        return {
            "raw": error_msg,
            "html": f'<div class="error-message">{error_msg}</div>',
            "mode": "focus"
        }

def _format_nahida_html(reasoning: str, content: str) -> str:
    """
    将纳西妲的思考过程和回答包装成漂亮的 HTML
    """
    # 将 Markdown 转换为 HTML
    content_html = markdown.markdown(content, extensions=['fenced_code', 'tables', 'nl2br'])
    reasoning_html = markdown.markdown(reasoning, extensions=['fenced_code', 'nl2br'])
    
    html = f"""
    <div class="nahida-container">
        <!-- 思考过程 (默认展开) -->
        <div class="thinking-box">
            <details open>
                <summary>🍃 纳西妲的沉思 (DeepSeek深度思考)</summary>
                <div class="thinking-content">
                    {reasoning_html}
                </div>
            </details>
        </div>
        
        <!-- 最终回答 -->
        <div class="nahida-answer">
            <div class="nahida-badge">小吉祥草王的解答</div>
            <div class="markdown-content">{content_html}</div>
        </div>
    </div>
    """
    return html