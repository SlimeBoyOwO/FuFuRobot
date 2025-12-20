# backend/database/operations.py
import sqlite3
import datetime
from typing import List, Dict, Any, Tuple

from backend.database.connection import get_connection

def execute_sql_query(sql_query: str) -> Tuple[List[Dict], str]:
    """
    执行 SQL 查询并返回可序列化的数据
    支持 SELECT/INSERT/UPDATE/DELETE 操作
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # 记录SQL类型
            sql_upper = sql_query.strip().upper()
            
            # 执行SQL
            cursor.execute(sql_query)
            
            # 根据SQL类型处理结果
            if sql_upper.startswith("SELECT"):
                # 获取列名
                columns = [description[0] for description in cursor.description] if cursor.description else []
                
                # 获取数据
                rows = cursor.fetchall()
                
                # 转换为字典列表
                result = []
                for row in rows:
                    row_dict = {}
                    for i, col in enumerate(columns):
                        value = row[i]
                        # 转换不可序列化的类型
                        if isinstance(value, (datetime.date, datetime.datetime)):
                            value = str(value)
                        elif hasattr(value, 'item'):  # numpy类型
                            value = value.item()
                        row_dict[col] = value
                    result.append(row_dict)
                
                conn.commit()
                return result, None
                
            elif sql_upper.startswith("INSERT"):
                # 获取插入的ID
                last_id = cursor.lastrowid
                conn.commit()
                
                # 返回插入结果信息
                result = [{
                    "operation": "INSERT",
                    "affected_rows": cursor.rowcount,
                    "last_insert_id": last_id,
                    "message": f"成功插入 {cursor.rowcount} 条记录"
                }]
                return result, None
                
            elif sql_upper.startswith("UPDATE"):
                affected_rows = cursor.rowcount
                conn.commit()
                
                # 返回更新结果信息
                result = [{
                    "operation": "UPDATE",
                    "affected_rows": affected_rows,
                    "message": f"成功更新 {affected_rows} 条记录"
                }]
                return result, None
                
            elif sql_upper.startswith("DELETE"):
                affected_rows = cursor.rowcount
                conn.commit()
                
                # 返回删除结果信息
                result = [{
                    "operation": "DELETE",
                    "affected_rows": affected_rows,
                    "message": f"成功删除 {affected_rows} 条记录"
                }]
                return result, None
                
            else:
                # 其他SQL操作
                conn.commit()
                return [], "不支持的操作类型"
                
    except sqlite3.Error as e:
        error_msg = f"SQL执行错误: {str(e)}"
        print(f"SQL错误: {error_msg}")
        return [], error_msg
    except Exception as e:
        error_msg = f"执行SQL时发生未知错误: {str(e)}"
        print(f"未知错误: {error_msg}")
        return [], error_msg

def execute_safe_sql(sql_query: str) -> Dict[str, Any]:
    """
    安全执行SQL查询，返回详细的执行结果
    """
    data, error = execute_sql_query(sql_query)
    
    if error:
        return {
            "success": False,
            "data": [],
            "error": error,
            "sql_type": "ERROR"
        }
    
    # 判断SQL类型
    sql_upper = sql_query.strip().upper()
    if sql_upper.startswith("SELECT"):
        sql_type = "SELECT"
    elif sql_upper.startswith("INSERT"):
        sql_type = "INSERT"
    elif sql_upper.startswith("UPDATE"):
        sql_type = "UPDATE"
    elif sql_upper.startswith("DELETE"):
        sql_type = "DELETE"
    else:
        sql_type = "OTHER"
    
    return {
        "success": True,
        "data": data,
        "error": None,
        "sql_type": sql_type,
        "record_count": len(data) if isinstance(data, list) else 1
    }