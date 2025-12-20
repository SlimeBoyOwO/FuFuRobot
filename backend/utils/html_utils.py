# backend/llm/html_utils.py
import markdown

def markdown_to_html(markdown_text: str) -> str:
    """
    将Markdown转换为HTML，添加自定义样式类
    """
    # 扩展Markdown功能
    extensions = [
        'fenced_code',      # 代码块
        'tables',           # 表格
        'nl2br',            # 换行转换
        'sane_lists',       # 智能列表
    ]
    
    html = markdown.markdown(markdown_text, extensions=extensions)
    
    # 添加自定义CSS类
    html = html.replace('<table>', '<table class="markdown-table">')
    html = html.replace('<code>', '<code class="markdown-code">')
    html = html.replace('<pre>', '<pre class="markdown-pre">')
    html = html.replace('<ul>', '<ul class="markdown-list">')
    html = html.replace('<ol>', '<ol class="markdown-list">')
    html = html.replace('<blockquote>', '<blockquote class="markdown-quote">')
    
    # 为h1-h6添加类
    for i in range(1, 7):
        html = html.replace(f'<h{i}>', f'<h{i} class="markdown-h{i}">')
    
    return f'<div class="markdown-content">{html}</div>'

def create_sql_html(sql: str, sql_type: str = "查询") -> str:
    """
    为SQL生成HTML格式
    """
    sql_type = "查询" if sql.strip().upper().startswith("SELECT") else "操作"
    sql_html = f'''
    <div class="sql-query">
        <strong>生成的SQL ({sql_type}):</strong><br>
        <code class="sql-code">{sql}</code>
        <div class="sql-explanation">
            <small>提示：这是一个{_get_sql_explanation(sql)}</small>
        </div>
    </div>
    '''
    return sql_html

def create_error_html(error_msg: str, error_type: str = "error") -> str:
    """
    创建错误信息HTML
    """
    css_class = "error-message"
    if error_type == "warning":
        css_class = "warning-message"
    elif error_type == "info":
        css_class = "info-message"
    
    return f'<div class="{css_class}"><p>{error_msg}</p></div>'

def create_ai_response_html(response_text: str) -> str:
    """
    创建AI响应HTML
    """
    html_content = markdown_to_html(response_text)
    return f'<div class="ai-response">{html_content}</div>'

def _get_sql_explanation(sql: str) -> str:
    """获取SQL的解释"""
    sql_upper = sql.upper()
    
    if sql_upper.startswith("SELECT"):
        if "GROUP BY" in sql_upper:
            return "分组统计查询"
        elif "ORDER BY" in sql_upper:
            return "排序查询"
        elif "WHERE" in sql_upper:
            return "条件查询"
        else:
            return "全表查询"
    elif sql_upper.startswith("INSERT"):
        return "数据插入操作"
    elif sql_upper.startswith("UPDATE"):
        return "数据更新操作"
    elif sql_upper.startswith("DELETE"):
        return "数据删除操作"
    else:
        return "SQL操作"