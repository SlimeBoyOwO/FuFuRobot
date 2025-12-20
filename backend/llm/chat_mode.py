# backend/llm/chat_mode.py
import threading
from typing import Dict, Any, List
import requests
import json
from .memory_manager import memory_manager
from backend.utils import markdown_to_html, create_error_html
from backend.config import DEEPSEEK_API_KEY, DEEPSEEK_API_URL, DEEPSEEK_MODEL, FUFU_PROMPT

# 全局变量用于存储聊天历史
_chat_history = []
# 聊天历史最大消息数
Tough_Memory = 80

# 在启动时加载保存的对话上下文结尾，为了使其不忘记最近的话。
saved_context = memory_manager.get_saved_context()
if saved_context:
    _chat_history.extend(saved_context)
    print(f"🔄 [系统] 已恢复上次最后的 {len(saved_context)} 条对话记录")

def _call_deepseek_api(prompt: str, history: List[Dict[str, str]] = None, system_prompt: str = None) -> Dict[str, str]:
    """
    调用 DeepSeek API，返回原始Markdown和转换后的HTML
    """
    if not DEEPSEEK_API_KEY:
        raise ValueError("未设置 DEEPSEEK_API_KEY 环境变量")
    
    # 准备消息格式
    messages = []
    
    # 添加系统提示
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    
    # 如果有历史记录，添加到消息中
    if history:
        for msg in history:
            messages.append(msg)
    
    # 添加当前用户消息
    messages.append({"role": "user", "content": prompt})
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }
    
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": messages,
        "stream": False,
        "max_tokens": 2048,
        "temperature": 0.5
    }
    
    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # 提取 AI 回复
        if "choices" in data and len(data["choices"]) > 0:
            ai_reply = data["choices"][0]["message"]["content"]
            
            # 更新聊天历史
            _chat_history.append({"role": "user", "content": prompt})
            _chat_history.append({"role": "assistant", "content": ai_reply})
                
            # 限制单次的硬历史长度在40条以内
            if len(_chat_history) > Tough_Memory:
                _chat_history[:] = _chat_history[(0-Tough_Memory):]
            
            # 将Markdown转换为HTML
            html_content = markdown_to_html(ai_reply)
            
            return {
                "raw": ai_reply,
                "html": html_content
            }
        else:
            raise ValueError("API响应格式错误")
            
    except requests.exceptions.RequestException as e:
        raise Exception(f"API调用失败: {str(e)}")
    except (KeyError, IndexError) as e:
        raise Exception(f"解析API响应失败: {str(e)}")

def get_chat_response(user_input: str) -> Dict[str, str]:
    """
    获取AI聊天响应，返回包含raw和html格式的字典
    """
    # 如果没有设置 API 密钥，使用模拟模式
    if not DEEPSEEK_API_KEY:
        raw_response = f"【模拟AI】收到消息：'{user_input}'。要使用真实的DeepSeek API，请在.env文件中设置DEEPSEEK_API_KEY。"
        html_response = create_error_html(
            f'【模拟AI】收到消息："{user_input}"。要使用真实的DeepSeek API，请在.env文件中设置DEEPSEEK_API_KEY。',
            "info"
        )
        
        return {
            "raw": raw_response,
            "html": html_response
        }
    
    try:
        
        # 1. 准备 System Prompt (人设 + 长期的记忆点)
        memory_context = memory_manager.get_memory_context()
        full_system_prompt = FUFU_PROMPT + memory_context
        
        # 使用最近的聊天历史（最多最近的40轮对话）
        recent_history = _chat_history[(0-Tough_Memory):] 
        
        # 调用 DeepSeek API
        response = _call_deepseek_api(
            prompt=user_input, 
            history=recent_history, 
            system_prompt=full_system_prompt
        )
        
        # 这样无论何时关闭程序，最后10轮对话都会被记住，用于承接下次对话
        memory_manager.save_chat_context(_chat_history)
        
        # 启动后台线程进行长期记忆信息提取和存储
        if len(user_input) > 2: # 记忆太短的话不做存储和分析了
            thread = threading.Thread(
            target=_extract_info_background, 
            args=(user_input, response["raw"])
            )
            thread.daemon = True # 设置为守护线程
            thread.start()
        return response
        
    except Exception as e:
        error_msg = str(e)
        print(f"DeepSeek API调用失败: {error_msg}")
        
        # 如果错误是因为API密钥无效，给出提示
        if "401" in error_msg or "unauthorized" in error_msg.lower():
            error_raw = "【API密钥错误】请检查.env文件中的DEEPSEEK_API_KEY是否正确。"
            error_html = create_error_html("【API密钥错误】请检查.env文件中的DEEPSEEK_API_KEY是否正确。")
        elif "timeout" in error_msg.lower():
            error_raw = "【网络超时】API调用超时，请检查网络连接后重试。"
            error_html = create_error_html("【网络超时】API调用超时，请检查网络连接后重试。")
        else:
            error_raw = f"【API调用失败】{error_msg}。请稍后重试。"
            error_html = create_error_html(f"【API调用失败】{error_msg}。请稍后重试。")
        
        return {
            "raw": error_raw,
            "html": error_html
        }

def _extract_info_background(user_input: str, ai_reply: str):
    """
    后台任务：调用 LLM 分析用户输入，提取记忆，细化了兴趣、经历、人际关系等提取维度
    """
    try:
        # 获取当前的已知用户画像
        current_name = memory_manager.memory["user_profile"].get("name", "用户")
        # 定义提取专用的 System Prompt
        extraction_system_prompt = """
        你是一个专业的"记忆侧写师"。
        【当前场景】
        请分析以下完整的一轮对话，提取其中的关键记忆信息：
        【用户】: {user_input}
        【AI助手】: {ai_reply}
        你正在分析一段对话，对话双方是：
        1. 用户 (User)：名字可能是"{current_name}"，也可能在对话中自称其他名字（如"空"）。
        2. AI助手 (Assistant)：拥有特定人设（如"芙宁娜"）自称本芙，会有自己的房间、爱好和行为。
        我需要你对用户的各种信息，做出提取和分类，帮助AI更好地记住用户的特点,偏好，经历和动态，以便在后续对话中更好地理解用户。
        同时也要记录ai的记忆信息，帮助ai更好地理解自己的设定和行为。     
        【重要规则】
        ❌ 严禁混淆：不要把 AI 的爱好、房间、物品、经历记在用户头上！
           - 如果 AI 说 "我家有很多轻小说"，不要记录用户有轻小说。
           - 如果 AI 说 "我喜欢吃蛋糕"，不要记录用户喜欢蛋糕。
        ✅ 区分角色：确保用户和AI的属性、经历、喜好等信息不混淆。
           - 如果 AI 说 "我养了一只猫"，记录AI养了猫。
           
        【提取指南 - 请关注以下维度】
        1. 👤 基础画像 (Profile)：
           - 姓名、昵称、性别、年龄、生日
           - 职业、学校、专业、年级
           - 居住地、家乡
           - 情感状态（单身/恋爱/已婚）
        
        2. ❤️ 兴趣偏好 (Interests)：
           - 娱乐：喜欢的游戏(如原神)、电影、动漫、书籍
           - 饮食：口味偏好(辣/甜)、忌口、最爱的食物
           - 爱好：运动、乐器、旅行、收藏
           - 雷点：明确讨厌或害怕的事物

        3. 📅 人生经历与事件 (Experiences)：
           - 重要节点：考试(考研/公考)、升职、毕业、搬家
           - 当前目标：正在努力做的事情(如"正在减肥"、"准备雅思")
           - 过去成就：获得奖项、完成的项目

        4. 🏠 复杂的事情 (Complex Things)：
           - 工作：职业、工作内容、工作地点
           - 学习：专业、课程、成绩
           - 生活：居住地、家庭情况、兴趣爱好
           - 旅行：去过的地方、旅行计划
           - 家庭：家庭成员、家庭关系
           - 教育：学校、专业、学历
           - 健康：身体状况、健康状况、医疗经历

        5. 📕 近期动态 (lately_things)：
              - 最近正在进行或发生的事情（如"最近在学Python编程"、"昨晚玩了什么游戏"、"中午吃了什么？"）
              - 最近完成的任务（如"给ai（芙芙）带了草莓蛋糕"、"给ai（芙芙）买了新衣服"）
              - 近期的变化（如"刚搬到上海"）
              
        6. 🤖 AI状态 (AI State)：（ai的状态记录，不单单要从ai的回复中提取，也建议从用户的输入中提取。）
           - AI的最近经历等信息（用户和ai一起的经历，ai单独的经历都可以记录）
           - AI的房间、物品、爱好、行为等设定细节
           - AI的当前状态（如"今天心情不错"、"今天有点累"）
           - AI的近期动态（如"刚刚在写故事"、"刚刚在听音乐"）
           - AI的最近吃的食物（如"刚刚吃了草莓蛋糕"、"刚刚吃了披萨"）
           - AI的最近做的行为（如"和用户一起和咖啡，喝奶茶"、"和用户一起看电影"）
           - AI的最近想吃的食物（如"想吃慕斯蛋糕"、"想吃披萨"）

        7. ❗ 废话过滤：
           - 只有当【用户输入】和【AI回复】都没有包含任何值得记忆的信息（如仅是寒暄"你好"、"再见"）时，才返回空对象。
           - ⚠️ 注意：如果用户只说了"你好"，但AI回复中包含了新的状态信息（如"我正在看书"），请务必记录 ai_state！
           
        【输出格式要求】
        请返回一个纯 JSON 对象，不要包含 Markdown 标记。
        - 将属性类信息（姓名、喜好、职业）放入 "profile"。
        - 将事件类、经历类、复杂的描述放入 "facts"。
        - 将一些最近发生的用户动态放入 "lately_things"，以便AI记住近期动态。
        - 将AI的状态信息放入 "ai_state"。
        - 返回的 JSON 对象中，不要包含任何非 JSON 格式的数据，例如 HTML、Markdown 等。

        JSON 结构示例：
        {
            "profile": {
                "name": "阿伟",
                "hobby_game": "原神",
                "food_preference": "喜欢吃火锅，不吃香菜",
                "major": "计算机科学"
            }, 
            "facts": [
                "用户养了一只叫'煤球'的黑猫",
                "用户计划在2024年底参加考研",
                "用户曾在高中时期获得过游泳冠军",
                "用户有一个妹妹,现在在上小学",
                "用户在大学里有一个好朋友"
            ],
            "lately_things": [
                "用户最近在研究Python编程",
                "用户刚刚搬到了上海",
                "用户昨晚玩了通宵的原神"
            ]
            "ai_state": [
                "ai最近吃了个草莓蛋糕",
                "ai刚刚和用户一起看了电影",
                "ai和用户一起喝了咖啡",
                "ai和用户说想吃慕斯蛋糕"
            ]
        }
    
        如果这句话全是废话（如"你好"、"哈哈"、"嗯嗯"），则直接返回空对象：
        { "profile": {}, "facts": [],lately_things": [], "ai_state": [] }
        """

        # 构造 prompt
        prompt = f"用户说：'{user_input}'\n(上下文参考 - AI回复：'{ai_reply}')"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
        }
        
        payload = {
            "model": DEEPSEEK_MODEL,
            "messages": [
                {"role": "system", "content": extraction_system_prompt},
                {"role": "user", "content": prompt}
            ],
        
            "temperature": 0.5, 
            "response_format": {"type": "json_object"}
        }
        
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=20)
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            # 清理 Markdown
            content = content.replace("```json", "").replace("```", "").strip()
            
            # 解析 JSON
            try:
                data = json.loads(content)
                
                # 1. 更新画像 (Profile)
                if "profile" in data and isinstance(data["profile"], dict):
                    for k, v in data["profile"].items():
                        # 过滤掉空值
                        if v: 
                            memory_manager.update_profile(k, str(v))
                
                # 2. 更新事实 (Facts)
                if "facts" in data and isinstance(data["facts"], list):
                    for fact in data["facts"]:
                        if fact:
                            memory_manager.add_fact(str(fact))
                            
                # 3. 更新近期动态 (Lately Things)
                if "lately_things" in data and isinstance(data["lately_things"], list):
                    for thing in data["lately_things"]:
                        if thing:
                            memory_manager.add_lately_thing(str(thing))

                # 4. 更新AI状态信息 (AI State)
                if "ai_state" in data and isinstance(data["ai_state"], list):
                    for state in data["ai_state"]:
                        # 过滤掉空值
                        if state: 
                            memory_manager.add_ai_state(str(state))
                        
            except json.JSONDecodeError:
                print(f"⚠️ 记忆提取失败: JSON解析错误 - {content}")
                
    except Exception as e:
        print(f"⚠️ 后台记忆提取出错: {e}")

def clear_chat_history() -> bool:
    """清除聊天历史"""
    global _chat_history
    _chat_history.clear()
    return True

def get_chat_history_length() -> int:
    """获取聊天历史长度"""
    return len(_chat_history)