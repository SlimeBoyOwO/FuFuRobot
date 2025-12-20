# backend/utils/helpers.py
import time
import random
import string
import re
from datetime import datetime

def format_time(timestamp: float = None, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """格式化时间"""
    if timestamp is None:
        timestamp = time.time()
    return datetime.fromtimestamp(timestamp).strftime(format_str)

def validate_email(email: str) -> bool:
    """验证邮箱格式"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def generate_random_id(length: int = 8) -> str:
    """生成随机ID"""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))