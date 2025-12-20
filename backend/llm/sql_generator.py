# backend/llm/sql_generator.py
import os
import sys
import re
import requests
import random
import time
from typing import Dict, Any
import json

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from config import DB_SCHEMA, DEEPSEEK_API_KEY, DEEPSEEK_API_URL, DEEPSEEK_MODEL

def generate_sql_with_ai(user_input: str) -> str:
    """
    使用AI生成SQL查询
    先尝试调用AI，失败则降级到规则匹配
    """
    # 检查API密钥
    if not DEEPSEEK_API_KEY or DEEPSEEK_API_KEY == "your_api_key_here":
        print("⚠️ API密钥未配置或为默认值，使用规则匹配")
        return _generate_sql_by_rules(user_input)
    
    try:
        print(f"🤖 使用AI生成SQL: {user_input}")
        # 尝试调用AI生成SQL
        sql = _call_deepseek_for_sql(user_input)
        
        # 验证SQL是否有效
        if _is_valid_sql(sql):
            print(f"✅ AI生成的SQL: {sql}")
            return sql
        else:
            print(f"⚠️ AI生成的SQL可能无效，降级到规则匹配: {sql}")
            return _generate_sql_by_rules(user_input)
            
    except Exception as e:
        print(f"❌ AI生成SQL失败，降级到规则匹配: {e}")
        # 降级到规则匹配
        return _generate_sql_by_rules(user_input)

def _call_deepseek_for_sql(user_input: str) -> str:
    """
    调用DeepSeek API生成SQL
    """
    # 构建系统提示
    system_prompt = f"""你是一个专业的SQL生成助手。根据用户的问题生成SQLite SQL查询语句。

数据库结构：
表名：students
字段列表：
{_format_table_schema()}

示例数据：
{_format_sample_data()}

生成规则：
1. 只返回纯SQL语句，不要任何解释、注释或Markdown标记
2. 使用正确的SQLite语法
3. 如果用户询问统计、数量、人数，请使用COUNT()和GROUP BY
4. 如果用户询问排序，请使用ORDER BY
5. 如果用户询问特定条件，请使用WHERE
6. 如果用户没有明确要求数量限制，默认返回给出所有数据
7. 列名使用英文，但可以使用AS起中文别名
8. 对于统计查询，请按用户要求的分组字段进行GROUP BY
9. 数值统计按降序排列，其他按需求排列
10. 对于INSERT语句，必须提供完整的VALUES数据
11. 查看学校招生人数变化，就是查看学生年级分布情况

重要：只返回SQL语句，不要其他任何内容！"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"请为以下问题生成SQL查询：{user_input}"}
    ]
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }
    
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": messages,
        "stream": False,
        "max_tokens": 800,  # 增加token数量，确保INSERT语句完整
        "temperature": 0.1,  # 低温度确保稳定输出
        "top_p": 0.9
    }
    
    try:
        response = requests.post(
            DEEPSEEK_API_URL, 
            headers=headers, 
            json=payload, 
            timeout=30
        )
        response.raise_for_status()
        
        data = response.json()
        
        if "choices" not in data or len(data["choices"]) == 0:
            raise ValueError("API响应格式错误")
        
        sql = data["choices"][0]["message"]["content"].strip()
        
        # 清理SQL响应
        sql = _clean_sql_response(sql)
        
        return sql
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"API请求失败: {str(e)}")
    except (KeyError, IndexError, ValueError) as e:
        raise Exception(f"解析API响应失败: {str(e)}")

def _clean_sql_response(sql: str) -> str:
    """
    清理AI返回的SQL，移除不必要的标记和解释
    """
    # 移除SQL代码块标记
    sql = re.sub(r'```sql\s*', '', sql)
    sql = re.sub(r'```\s*', '', sql)
    
    # 移除可能的"SELECT"之前的文本
    lines = sql.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line_stripped = line.strip()
        
        # 跳过明显的非SQL行
        if line_stripped and not line_stripped.startswith(('--', '/*', '*/', '#')):
            # 查找第一个SQL关键词的位置
            sql_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'WITH', 'CREATE', 'ALTER', 'DROP']
            for keyword in sql_keywords:
                idx = line_stripped.upper().find(keyword)
                if idx != -1:
                    cleaned_lines.append(line_stripped[idx:])
                    break
            else:
                # 如果没有找到SQL关键词，但看起来像SQL，保留
                if any(word in line_stripped.upper() for word in ['FROM', 'WHERE', 'GROUP', 'ORDER', 'LIMIT', 'JOIN']):
                    cleaned_lines.append(line_stripped)
    
    cleaned_sql = ' '.join(cleaned_lines).strip()
    
    # ========== 新增：针对INSERT语句的特判和补全 ==========
    sql_upper = cleaned_sql.upper()
    if sql_upper.startswith("INSERT"):
        print(f"🔍 检测到INSERT语句，进行完整性检查...")
        
        # 检查INSERT语句是否完整
        if not _is_insert_sql_complete(cleaned_sql):
            print(f"⚠️ INSERT语句不完整，尝试使用备用规则生成")
            
            # 根据用户输入判断是否需要生成随机学生
            user_input_lower = ""  # 这里需要从调用上下文获取，暂时设为空
            
            # 检查是否包含"随机"或"2024级"等关键词
            # 注意：这里需要从外部获取user_input，暂时使用简单判断
            # 在实际调用中，可以考虑将user_input传递给这个函数
            
            # 调用随机插入生成函数
            return _generate_random_insert_sql()
    
    # 如果没有有效的SQL，使用默认
    if not cleaned_sql or not cleaned_sql.upper().startswith(('SELECT', 'INSERT', 'UPDATE', 'DELETE')):
        cleaned_sql = "SELECT * FROM students LIMIT 10"
    
    return cleaned_sql

def _is_insert_sql_complete(sql: str) -> bool:
    """
    检查INSERT语句是否完整
    新增：专门用于检查INSERT语句的完整性
    """
    sql_upper = sql.upper().strip()
    
    # 检查基本结构
    if not sql_upper.startswith("INSERT"):
        return False
    
    # 必须包含INTO和VALUES关键字
    if "INTO" not in sql_upper or "VALUES" not in sql_upper:
        return False
    
    # 找到VALUES关键字的位置
    values_index = sql_upper.find("VALUES")
    if values_index == -1:
        return False
    
    # 获取VALUES之后的部分
    values_part = sql[values_index + 6:].strip()  # "VALUES"长度为6
    
    # VALUES之后必须有内容
    if not values_part:
        return False
    
    # VALUES之后应该以括号开头
    if not values_part.startswith('('):
        return False
    
    # 检查括号是否匹配
    open_count = values_part.count('(')
    close_count = values_part.count(')')
    
    # 闭合括号数应该至少等于开放括号数
    if close_count < open_count:
        return False
    
    # 检查是否有具体的值（至少有一个逗号，除非只有一条记录）
    if ',' not in values_part and ')' in values_part:
        # 只有一条记录的情况，检查括号内是否有内容
        start = values_part.find('(')
        end = values_part.find(')')
        if start != -1 and end != -1 and start < end:
            content = values_part[start+1:end].strip()
            if not content:
                return False
    
    return True

def _is_valid_sql(sql: str) -> bool:
    """
    简单验证SQL是否有效
    """
    sql_upper = sql.upper().strip()
    
    # 检查是否是有效的SQL语句
    if not sql_upper:
        return False
    
    # 检查是否以SQL关键词开头
    if not sql_upper.startswith(('SELECT', 'INSERT', 'UPDATE', 'DELETE', 'WITH')):
        return False
    
    # ========== 新增：针对INSERT语句的专项检查 ==========
    if sql_upper.startswith("INSERT"):
        return _is_insert_sql_complete(sql)
    
    # 检查是否包含表名（对于非INSERT语句）
    if 'STUDENTS' not in sql_upper:
        # 对于SELECT * FROM students这种，可能有大写小写问题
        if 'FROM' in sql_upper:
            # 简单的FROM验证
            pass
        else:
            return False
    
    return True

def _generate_random_insert_sql() -> str:
    """
    生成随机插入学生的SQL语句（可靠的备用方案）
    新增：专门处理随机插入学生的请求
    """
    # 随机信息池
    first_names = ["张", "王", "李", "赵", "刘", "陈", "杨", "黄", "周", "吴", "郑", "孙", "钱", "冯", "程"]
    last_names = ["伟", "芳", "娜", "秀英", "敏", "静", "磊", "强", "洋", "艳", "明", "华", "军", "杰", "婷"]
    classes = ["一班", "二班", "三班", "四班", "五班"]
    colleges = ["计算机学院", "经管学院", "文学院", "理学院", "医学院", "法学院", "艺术学院"]
    majors = ["软件工程", "人工智能", "数据科学", "计算机科学", "物联网工程", "会计学", "金融学", "临床医学", "法学", "汉语言文学"]
    
    # 生成两个不同的学号（基于时间戳加随机数，降低冲突概率）
    base_id = int(time.time()) % 10000
    student_id_1 = f"2024{base_id + random.randint(1, 50):04d}"
    student_id_2 = f"2024{base_id + random.randint(51, 100):04d}"
    
    # 生成第一条记录
    name1 = random.choice(first_names) + random.choice(last_names)
    class1 = random.choice(classes)
    college1 = random.choice(colleges)
    major1 = random.choice(majors)
    gender1 = random.choice(["男", "女"])
    phone1 = f"138{random.randint(1000, 9999):04d}{random.randint(1000, 9999):04d}"
    
    # 生成第二条记录（确保与第一条不完全相同）
    name2 = random.choice(first_names) + random.choice(last_names)
    while name2 == name1:  # 确保姓名不同
        name2 = random.choice(first_names) + random.choice(last_names)
    
    class2 = random.choice(classes)
    college2 = random.choice(colleges)
    major2 = random.choice(majors)
    gender2 = random.choice(["男", "女"])
    phone2 = f"139{random.randint(1000, 9999):04d}{random.randint(1000, 9999):04d}"
    
    # 构建完整的INSERT语句
    sql = f"""INSERT INTO students (name, student_id, class_name, college, major, grade, gender, phone) VALUES
('{name1}', '{student_id_1}', '{class1}', '{college1}', '{major1}', '2024级', '{gender1}', '{phone1}'),
('{name2}', '{student_id_2}', '{class2}', '{college2}', '{major2}', '2024级', '{gender2}', '{phone2}')"""
    
    print(f"✅ 使用备用规则生成随机插入SQL")
    return sql

def _generate_sql_by_rules(user_input: str) -> str:
    """
    规则匹配生成SQL（降级方案）
    增强版：支持更复杂的查询
    """
    user_input_lower = user_input.lower()
    
    # ========== 新增：专门处理随机插入的请求 ==========
    if "随机" in user_input_lower and "插入" in user_input_lower and "学生" in user_input_lower:
        if "2024级" in user_input or "2024" in user_input:
            print("🎲 检测到随机插入2024级学生请求，使用规则生成")
            return _generate_random_insert_sql()
        else:
            # 默认插入2名学生
            return _generate_random_insert_sql()
    
    # 1. 统计类查询（增强）
    if any(keyword in user_input_lower for keyword in ["统计", "计数", "多少", "人数", "数量", "分布"]):
        # 专业人数统计（如：查看计算机学院不同专业人数）
        if "专业" in user_input_lower and "学院" in user_input_lower:
            # 提取学院名称
            college_patterns = [
                r'([\u4e00-\u9fa5]+学院)',
                r'学院[：:]?\s*([\u4e00-\u9fa5]+)',
                r'([\u4e00-\u9fa5]+)学院'
            ]
            college = "计算机学院"  # 默认
            for pattern in college_patterns:
                match = re.search(pattern, user_input)
                if match:
                    college = match.group(1)
                    break
            
            return f"SELECT major, COUNT(*) as 人数 FROM students WHERE college = '{college}' GROUP BY major ORDER BY 人数 DESC"
        
        # 学院人数统计
        elif "学院" in user_input_lower:
            return "SELECT college, COUNT(*) as 人数 FROM students GROUP BY college ORDER BY 人数 DESC"
        
        # 专业人数统计
        elif "专业" in user_input_lower:
            return "SELECT major, COUNT(*) as 人数 FROM students GROUP BY major ORDER BY 人数 DESC"
        
        # 班级人数统计
        elif "班级" in user_input_lower:
            return "SELECT class_name, COUNT(*) as 人数 FROM students GROUP BY class_name ORDER BY 人数 DESC"
        
        # 年级人数统计
        elif "年级" in user_input_lower:
            return "SELECT grade, COUNT(*) as 人数 FROM students GROUP BY grade ORDER BY 人数 DESC"
        
        # 性别统计
        elif "性别" in user_input_lower:
            return "SELECT gender, COUNT(*) as 人数 FROM students GROUP BY gender"
        
        # 总人数
        else:
            return "SELECT COUNT(*) as 总人数 FROM students"
    
    # 2. 查询类（增强）
    elif any(keyword in user_input_lower for keyword in ["查询", "查看", "显示", "找", "列出", "显示所有", "查看所有"]):
        # 学院查询
        college_mapping = {
            "计算机": "计算机学院",
            "经管": "经管学院",
            "经管学院": "经管学院",
            "计算机学院": "计算机学院",
            "文学院": "文学院",
            "理学院": "理学院",
            "医学院": "医学院"
        }
        
        for keyword, college_name in college_mapping.items():
            if keyword in user_input:
                return f"SELECT * FROM students WHERE college = '{college_name}'"
        
        # 专业查询
        major_mapping = {
            "软件工程": "软件工程",
            "会计学": "会计学",
            "计算机科学": "计算机科学",
            "人工智能": "人工智能",
            "金融学": "金融学",
            "临床医学": "临床医学"
        }
        
        for keyword, major_name in major_mapping.items():
            if keyword in user_input:
                return f"SELECT * FROM students WHERE major = '{major_name}'"
        
        # 年级查询
        grade_mapping = {
            "2022级": "2022级",
            "2023级": "2023级",
            "2024级": "2024级",
            "大一": "2024级",
            "大二": "2023级",
            "大三": "2022级"
        }
        
        for keyword, grade_name in grade_mapping.items():
            if keyword in user_input_lower:
                return f"SELECT * FROM students WHERE grade = '{grade_name}'"
        
        # 性别查询
        if "男生" in user_input_lower or "男同学" in user_input_lower:
            return "SELECT * FROM students WHERE gender = '男'"
        elif "女生" in user_input_lower or "女同学" in user_input_lower:
            return "SELECT * FROM students WHERE gender = '女'"
        
        # 班级查询
        class_pattern = r'([一二三四五六七八九十\d]+班)'
        match = re.search(class_pattern, user_input)
        if match:
            class_name = match.group(1)
            return f"SELECT * FROM students WHERE class_name = '{class_name}'"
        
        # 综合查询：包含多个条件
        conditions = []
        
        # 学院条件
        for keyword, college_name in college_mapping.items():
            if keyword in user_input:
                conditions.append(f"college = '{college_name}'")
        
        # 专业条件
        for keyword, major_name in major_mapping.items():
            if keyword in user_input:
                conditions.append(f"major = '{major_name}'")
        
        # 年级条件
        for keyword, grade_name in grade_mapping.items():
            if keyword in user_input_lower:
                conditions.append(f"grade = '{grade_name}'")
        
        # 性别条件
        if "男生" in user_input_lower:
            conditions.append("gender = '男'")
        elif "女生" in user_input_lower:
            conditions.append("gender = '女'")
        
        # 构建查询
        if conditions:
            where_clause = " AND ".join(conditions)
            return f"SELECT * FROM students WHERE {where_clause} LIMIT 20"
        else:
            return "SELECT * FROM students LIMIT 20"
    
    # 3. 排序类
    elif any(keyword in user_input_lower for keyword in ["排序", "按", "顺序", "排名"]):
        order = "DESC" if "降序" in user_input_lower or "从大到小" in user_input_lower else "ASC"
        
        if "学号" in user_input_lower:
            return f"SELECT * FROM students ORDER BY student_id {order}"
        elif "姓名" in user_input_lower:
            return f"SELECT * FROM students ORDER BY name {order}"
        elif "成绩" in user_input_lower or "分数" in user_input_lower:
            # 如果没有成绩字段，按ID排序
            return f"SELECT * FROM students ORDER BY id {order}"
        elif "时间" in user_input_lower or "创建" in user_input_lower:
            return f"SELECT * FROM students ORDER BY created_at {order}"
        else:
            return f"SELECT * FROM students ORDER BY id {order}"
    
    # 4. 新增学生
    elif any(keyword in user_input_lower for keyword in ["新增", "添加", "创建", "插入", "增加"]):
        if "学生" in user_input_lower:
            # 检查是否包含"随机"关键词
            if "随机" in user_input_lower:
                return _generate_random_insert_sql()
            
            # 提取学生信息（简化版）
            name_pattern = r'叫([\u4e00-\u9fa5]{2,4})'
            match = re.search(name_pattern, user_input)
            name = match.group(1) if match else "新学生"
            
            # 尝试提取年级
            grade = "2023级"
            if "2024" in user_input or "2024级" in user_input:
                grade = "2024级"
            elif "2022" in user_input or "2022级" in user_input:
                grade = "2022级"
            
            return f"""INSERT INTO students (name, student_id, class_name, college, major, grade, gender, phone) 
VALUES ('{name}', '2023999', '一班', '计算机学院', '软件工程', '{grade}', '男', '13800000000')"""
    
    # 5. 更新信息
    elif any(keyword in user_input_lower for keyword in ["修改", "更新", "更改", "编辑"]):
        name_pattern = r'([\u4e00-\u9fa5]{2,4})'
        match = re.search(name_pattern, user_input)
        if match:
            name = match.group(1)
            
            if "电话" in user_input_lower or "手机" in user_input_lower:
                phone_pattern = r'(\d{11})'
                phone_match = re.search(phone_pattern, user_input)
                phone = phone_match.group(1) if phone_match else '13899999999'
                return f"UPDATE students SET phone = '{phone}' WHERE name = '{name}'"
            elif "班级" in user_input_lower:
                class_pattern = r'([一二三四五六七八九十\d]+班)'
                class_match = re.search(class_pattern, user_input)
                class_name = class_match.group(1) if class_match else '一班'
                return f"UPDATE students SET class_name = '{class_name}' WHERE name = '{name}'"
    
    # 6. 删除信息
    elif any(keyword in user_input_lower for keyword in ["删除", "移除", "去掉", "清除"]):
        return "-- 删除操作需要谨慎，请提供具体的删除条件"
    
    # 7. 复杂查询：组合条件
    elif any(keyword in user_input_lower for keyword in ["并且", "且", "同时", "还", "又要"]):
        # 尝试处理组合条件
        conditions = []
        
        if "男生" in user_input_lower:
            conditions.append("gender = '男'")
        elif "女生" in user_input_lower:
            conditions.append("gender = '女'")
        
        if "计算机学院" in user_input:
            conditions.append("college = '计算机学院'")
        elif "经管学院" in user_input:
            conditions.append("college = '经管学院'")
        
        if conditions:
            where_clause = "AND".join(conditions)
            return f"SELECT * FROM students WHERE {where_clause} LIMIT 20"
    
    # 默认查询
    return "SELECT * FROM students LIMIT 10"

def _format_table_schema() -> str:
    """格式化表结构信息"""
    schema_text = ""
    for column in DB_SCHEMA["students"]["columns"]:
        schema_text += f"- {column['name']} ({column['type']}): {column['description']}\n"
    return schema_text

def _format_sample_data() -> str:
    """格式化示例数据"""
    sample_text = ""
    for i, data in enumerate(DB_SCHEMA["students"]["sample_data"], 1):
        sample_text += f"- 示例{i}: {data}\n"
    return sample_text

# 测试函数
def test_sql_generation():
    """测试SQL生成"""
    test_cases = [
        "随机插入2名2024级的学生",
        "查看计算机学院不同专业人数，按专业划分",
        "统计各学院人数",
        "查询所有男生信息",
        "查找软件工程专业的学生",
        "显示2023级的学生，按学号排序",
        "查看计算机学院的男生",
        "统计各专业人数并按人数降序排列",
        "查询所有学生信息，按创建时间倒序"
    ]
    
    for test_input in test_cases:
        print(f"\n测试输入: {test_input}")
        try:
            sql = generate_sql_with_ai(test_input)
            print(f"生成的SQL: {sql}")
        except Exception as e:
            print(f"错误: {e}")

if __name__ == "__main__":
    # 运行测试
    test_sql_generation()