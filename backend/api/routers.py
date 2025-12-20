# backend/api/routers.py
from fastapi import APIRouter, HTTPException
import datetime
import os,sys
import pandas as pd

from .schemas import (
    ChatRequest, ClearHistoryRequest, TestAPIRequest, 
    SQLExecuteRequest, HealthResponse, SystemInfoResponse, ChatResponse
)
from backend.database import (
    execute_safe_sql, get_table_info, check_db_connection
)

from backend.llm import (
    clear_chat_history, get_chat_history_length, analyze_data_for_chart,get_nahida_response,
    get_chat_response, get_db_response
)

from backend.config import DEEPSEEK_API_KEY

router = APIRouter(prefix="/api", tags=["api"])

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": "ai-student-management",
        "version": "2.0.0",
        "timestamp": datetime.datetime.now().isoformat(),
        "chat_history_length": get_chat_history_length(),
        "database": "connected" if check_db_connection()[0] else "disconnected"
    }

@router.get("/system-info", response_model=SystemInfoResponse)
async def system_info():
    """系统信息端点"""
    return {
        "deepseek_api_configured": bool(DEEPSEEK_API_KEY),
        "chat_history_messages": get_chat_history_length(),
        "environment": "development",
        "database": "sqlite3",
        "features": ["chat", "text2sql", "charts", "crud_operations"]
    }

@router.get("/db-info")
async def db_info():
    """获取数据库信息"""
    return get_table_info()

@router.post("/test-api")
async def test_api_endpoint(request: TestAPIRequest):
    """测试DeepSeek API端点"""
    try:
        test_message = request.test_message
        response = get_chat_response(test_message)
        
        return {
            "success": True,
            "test_message": test_message,
            "raw_response": response["raw"],
            "html_response": response["html"],
            "api_configured": bool(DEEPSEEK_API_KEY)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"测试失败: {str(e)}")

@router.post("/execute-sql")
async def execute_sql_endpoint(request: SQLExecuteRequest):
    """直接执行SQL语句"""
    sql = request.sql.strip()
    
    if not sql:
        return {
            "success": False,
            "error": "SQL语句不能为空"
        }
    
    try:
        result = execute_safe_sql(sql)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行SQL失败: {str(e)}")

@router.post("/clear-history")
async def clear_history_endpoint(request: ClearHistoryRequest):
    """清除聊天历史"""
    try:
        if clear_chat_history():
            return {
                "success": True,
                "message": "聊天历史已清除",
                "history_length": get_chat_history_length()
            }
        else:
            return {
                "success": False,
                "message": "聊天历史清除失败",
                "history_length": get_chat_history_length()
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清除历史失败: {str(e)}")

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    user_input = request.message.strip()
    mode = request.mode
    
    if not user_input:
        return {
            "success": False,
            "text": "请输入有效的问题",
            "html": '<div class="error"><p>请输入有效的问题</p></div>',
            "sql": None,
            "data": [],
            "chart_config": {},
            "chart_type": "none",
            "operation_result": None,
            "mode": mode
        }
    
    result = {
        "success": True,
        "text": "",           # 原始文本
        "html": "",          # HTML格式内容
        "sql": None, 
        "data": [],
        "chart_config": {},
        "chart_type": "none",
        "operation_result": None,  # 操作结果（用于INSERT/UPDATE/DELETE）
        "mode": mode
    }
    
    try:
        if mode == "chat":
            # 使用DeepSeek API进行聊天
            response = get_chat_response(user_input)
            result["text"] = response["raw"]
            result["html"] = response["html"]
        elif mode == "focus":
            # 2. 新增的纳西妲模式 (无记忆，深度思考)
            response = get_nahida_response(user_input)
            result["text"] = response["raw"]
            result["html"] = response["html"]
            # 纳西妲模式不涉及 SQL 操作，所以不需要后续逻辑
        elif mode == "text2sql":
            # 使用AI生成SQL
            response = get_db_response(user_input)
            sql_query = response["raw"]
            
            # 执行SQL查询获取数据
            sql_result = execute_safe_sql(sql_query)
            
            if not sql_result["success"]:
                result["success"] = False
                result["text"] = f"SQL执行错误: {sql_result['error']}"
                result["html"] = f'<div class="error"><p>SQL执行错误: {sql_result["error"]}</p></div>'
                result["html"] += response["html"]  # 仍然显示生成的SQL
            else:
                result["sql"] = sql_query
                result["data"] = sql_result["data"]
                result["html"] = response["html"]  # 显示SQL查询
                
                # 根据SQL类型处理
                if sql_result["sql_type"] == "SELECT":
                    # 对于查询，进行图表分析
                    df = pd.DataFrame(sql_result["data"]) if sql_result["data"] else pd.DataFrame()
                    
                    # 传递用户输入给图表分析函数
                    chart_info = analyze_data_for_chart(df, sql_query, user_input)
                    
                    result["chart_type"] = chart_info["chart_type"]
                    result["chart_config"] = chart_info["config"]
                    
                    # 生成文本总结
                    record_count = len(sql_result["data"])
                    summary = f"查询成功！找到 {record_count} 条记录。"
                    
                    # 添加图表信息
                    if chart_info.get("instruction_followed"):
                        summary += f" 已按您的要求生成{chart_info.get('explicit_instruction', {}).get('explicit_chart_name', '图表')}。"
                    elif chart_info["chart_type"] != "none" and chart_info["chart_type"] != "table":
                        chart_names = {
                            "bar_chart": "柱状图",
                            "line_chart": "折线图",
                            "pie_chart": "饼图",
                            "scatter_chart": "散点图",
                            "multi_bar_chart": "多系列柱状图"
                        }
                        chart_name = chart_names.get(chart_info["chart_type"], "图表")
                        summary += f" 智能推荐使用{chart_name}展示。"
                    
                    result["text"] = summary
                    
                    # 添加总结到HTML
                    result["html"] += f'<div class="query-summary"><p>{summary}</p></div>'
                
                else:
                    # 对于增删改操作，显示操作结果
                    operation_data = sql_result["data"][0] if sql_result["data"] else {}
                    result["operation_result"] = operation_data
                    
                    operation_type = sql_result["sql_type"]
                    if operation_type == "INSERT":
                        result["text"] = f"插入成功！{operation_data.get('message', '记录已添加')}"
                    elif operation_type == "UPDATE":
                        result["text"] = f"更新成功！{operation_data.get('message', '记录已更新')}"
                    elif operation_type == "DELETE":
                        result["text"] = f"删除成功！{operation_data.get('message', '记录已删除')}"
                    
                    # 添加操作结果到HTML
                    result["html"] += f'''
                    <div class="operation-result success">
                        <p>{result["text"]}</p>
                        <small>操作类型: {operation_type}</small>
                    </div>
                    '''
        
        else:
            result["success"] = False
            result["text"] = f"未知的模式: {mode}"
            result["html"] = f'<div class="error"><p>未知的模式: {mode}</p></div>'
                
    except Exception as e:
        error_msg = f"处理请求时发生错误: {str(e)}"
        print(f"API错误: {error_msg}")
        result["success"] = False
        result["text"] = error_msg
        result["html"] = f'<div class="error"><p>{error_msg}</p></div>'
    
    return result