# backend/api/schemas.py
from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    message: str
    mode: str  # 'chat' or 'text2sql'

class ClearHistoryRequest(BaseModel):
    confirm: bool = True

class TestAPIRequest(BaseModel):
    test_message: str = "你好，请介绍一下你自己"

class SQLExecuteRequest(BaseModel):
    sql: str

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str
    chat_history_length: int
    database: str

class SystemInfoResponse(BaseModel):
    deepseek_api_configured: bool
    chat_history_messages: int
    environment: str
    database: str
    features: list

class ChatResponse(BaseModel):
    success: bool
    text: str
    html: str
    sql: Optional[str] = None
    data: list = []
    chart_config: dict = {}
    chart_type: str = "none"
    operation_result: Optional[dict] = None
    mode: str