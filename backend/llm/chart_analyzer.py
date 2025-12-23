# backend/llm/chart_analyzer.py
import re
import pandas as pd
from typing import Dict, Any
import warnings

warnings.filterwarnings('ignore', category=UserWarning, module='pandas')

def analyze_data_for_chart(df: pd.DataFrame, sql: str = "", user_input: str = "") -> Dict[str, Any]:
    """
    智能分析数据，返回图表类型和建议配置
    增强版：支持用户指令和智能推荐
    """
    return analyze_data_for_chart_with_instruction(df, sql, user_input)

def analyze_data_for_chart_with_instruction(df: pd.DataFrame, sql: str, user_input: str = "") -> Dict[str, Any]:
    """
    智能分析数据，返回图表类型和配置
    1. 如果用户明确指定图表类型/要求，优先遵循
    2. 否则根据数据特征智能推荐
    """
    if df is None or df.empty:
        return {"chart_type": "none", "config": {}}
    
    # 分析用户指令
    instruction = _extract_chart_instruction(user_input)
    
    # 数据特征分析
    numeric_cols = []
    categorical_cols = []
    datetime_cols = []
    
    for col in df.columns:
        # 1. 先检查是否已经是数值类型
        if pd.api.types.is_numeric_dtype(df[col]):
            numeric_cols.append(col)
            continue
        
        # 2. 检查是否已经是日期时间类型
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            datetime_cols.append(col)
            continue
        
        # 3. 尝试转换为数值
        try:
            temp_numeric = pd.to_numeric(df[col], errors='coerce')
            if temp_numeric.notna().all():  # 或者使用某个比例阈值
                df[col] = temp_numeric
                numeric_cols.append(col)
                continue
        except:
            pass  # 继续尝试其他类型
        
        # 4. 尝试转换为日期时间
        try:
            temp_datetime = pd.to_datetime(df[col], errors='coerce', infer_datetime_format=True)
            if temp_datetime.notna().mean() > 0.5:  # 超过50%能转换
                df[col] = temp_datetime
                datetime_cols.append(col)
                continue
        except:
            pass  # 继续下一步
        
        # 5. 否则作为分类数据
        categorical_cols.append(col)
    
    # 构建默认配置
    default_config = {
        "title": "数据可视化",
        "show_title": True,
        "show_legend": len(numeric_cols) > 1 or len(categorical_cols) > 1,
        "animation": True
    }
    
    # 1. 用户明确指定了图表类型
    if instruction["explicit_chart_type"]:
        chart_type = instruction["explicit_chart_type"]
        
        # 根据用户选择的图表类型生成配置
        if chart_type == "bar_chart":
            config = _generate_bar_chart_config(df, instruction["requirements"], 
                                               numeric_cols, categorical_cols)
        elif chart_type == "line_chart":
            config = _generate_line_chart_config(df, instruction["requirements"], 
                                                numeric_cols, categorical_cols, datetime_cols)
        elif chart_type == "pie_chart":
            config = _generate_pie_chart_config(df, instruction["requirements"], 
                                               numeric_cols, categorical_cols)
        elif chart_type == "scatter_chart":
            config = _generate_scatter_chart_config(df, instruction["requirements"], 
                                                   numeric_cols, categorical_cols)
        else:
            # 其他图表类型使用智能推荐
            config = _get_smart_chart_config(df, sql, numeric_cols, categorical_cols, datetime_cols)
            chart_type = config.get("chart_type", "bar_chart")
        
        # 更新用户要求
        config.update(default_config)
        if "title" in instruction["requirements"]:
            config["title"] = instruction["requirements"]["title"]
        
        return {
            "chart_type": chart_type,
            "config": config,
            "instruction_followed": True,
            "explicit_instruction": instruction
        }
    
    # 2. 用户有特定要求但未指定图表类型
    elif instruction["requirements"]:
        # 根据用户要求和数据特征智能选择图表
        config = _get_chart_by_requirements(df, instruction["requirements"], 
                                          numeric_cols, categorical_cols, datetime_cols)
        config.update(default_config)
        
        return {
            "chart_type": config["chart_type"],
            "config": config,
            "instruction_followed": True,
            "explicit_instruction": instruction
        }
    
    # 3. 完全智能推荐（用户无明确要求）
    else:
        config = _get_smart_chart_config(df, sql, numeric_cols, categorical_cols, datetime_cols)
        config.update(default_config)
        
        return {
            "chart_type": config["chart_type"],
            "config": config,
            "instruction_followed": False,
            "explicit_instruction": instruction
        }

def _extract_chart_instruction(user_input: str) -> Dict[str, Any]:
    """
    从用户输入中提取图表指令
    返回格式: {"chart_type": "类型", "requirements": {具体要求}}
    """
    user_input_lower = user_input.lower()
    
    # 图表类型映射
    chart_keywords = {
        "柱状图": "bar_chart",
        "柱状": "bar_chart",
        "条形图": "bar_chart",
        "条形": "bar_chart",
        "折线图": "line_chart",
        "折线": "line_chart",
        "饼图": "pie_chart",
        "饼状图": "pie_chart",
        "散点图": "scatter_chart",
        "散点": "scatter_chart",
        "雷达图": "radar_chart",
        "雷达": "radar_chart",
        "热力图": "heatmap",
        "地图": "map_chart",
        "仪表盘": "gauge"
    }
    
    # 检查用户是否明确指定了图表类型
    explicit_chart_type = None
    explicit_chart_name = None
    
    for chinese_name, english_type in chart_keywords.items():
        if chinese_name in user_input:
            explicit_chart_type = english_type
            explicit_chart_name = chinese_name
            break
    
    # 检查是否有特定的绘图要求
    requirements = {}
    
    # 提取X轴要求
    x_axis_patterns = [
        r"以([^为]+)为.*[xX]轴",
        r"用([^做]+)做.*[xX]轴",
        r"[xX]轴.*用([^，。]+)",
        r"横轴.*是([^，。]+)"
    ]
    for pattern in x_axis_patterns:
        match = re.search(pattern, user_input)
        if match:
            requirements["x_axis"] = match.group(1).strip()
    
    # 提取Y轴要求
    y_axis_patterns = [
        r"以([^为]+)为.*[yY]轴",
        r"用([^做]+)做.*[yY]轴",
        r"[yY]轴.*用([^，。]+)",
        r"纵轴.*是([^，。]+)"
    ]
    for pattern in y_axis_patterns:
        match = re.search(pattern, user_input)
        if match:
            requirements["y_axis"] = match.group(1).strip()
    
    # 检查是否有其他要求
    if "排序" in user_input_lower:
        requirements["sorted"] = True
        if "升序" in user_input_lower or "从小到大" in user_input_lower:
            requirements["sort_order"] = "asc"
        elif "降序" in user_input_lower or "从大到小" in user_input_lower:
            requirements["sort_order"] = "desc"
    
    if "前" in user_input_lower and ("个" in user_input_lower or "名" in user_input_lower):
        # 提取前N个，如"前5个"
        match = re.search(r'前(\d+)(个|名)', user_input_lower)
        if match:
            requirements["limit"] = int(match.group(1))
    
    if "颜色" in user_input_lower:
        requirements["has_color_requirement"] = True
    
    if "标题" in user_input_lower:
        # 尝试提取标题
        title_match = re.search(r'标题[是：:]+([^，。]+)', user_input)
        if title_match:
            requirements["title"] = title_match.group(1).strip()
    
    return {
        "explicit_chart_type": explicit_chart_type,
        "explicit_chart_name": explicit_chart_name,
        "requirements": requirements,
        "has_chart_instruction": explicit_chart_type is not None or len(requirements) > 0
    }

def _generate_bar_chart_config(df, requirements, numeric_cols, categorical_cols):
    """生成柱状图配置"""
    config = {"chart_type": "bar_chart"}
    
    # 确定X轴
    if "x_axis" in requirements:
        config["x_axis"] = requirements["x_axis"]
    elif categorical_cols:
        config["x_axis"] = categorical_cols[0]
    else:
        config["x_axis"] = df.columns[0] if len(df.columns) > 0 else "category"
    
    # 确定Y轴
    if "y_axis" in requirements:
        config["y_axis"] = requirements["y_axis"]
    elif numeric_cols:
        config["y_axis"] = numeric_cols[0]
    else:
        # 如果没有数值列，使用计数
        config["y_axis"] = "count"
        config["show_values"] = True
    
    # 应用排序要求
    if requirements.get("sorted"):
        config["sorted"] = True
        config["sort_order"] = requirements.get("sort_order", "desc")
    
    # 应用限制
    if "limit" in requirements:
        config["limit"] = requirements["limit"]
    
    # 添加默认标题
    if "x_axis" in config and "y_axis" in config:
        config["title"] = f"{config['y_axis']} 按 {config['x_axis']} 统计"
    
    return config

def _generate_line_chart_config(df, requirements, numeric_cols, categorical_cols, datetime_cols):
    """生成折线图配置"""
    config = {"chart_type": "line_chart"}
    
    # 优先使用时间序列作为X轴
    if datetime_cols:
        config["x_axis"] = datetime_cols[0]
    elif "x_axis" in requirements:
        config["x_axis"] = requirements["x_axis"]
    elif categorical_cols:
        config["x_axis"] = categorical_cols[0]
    else:
        config["x_axis"] = df.columns[0] if len(df.columns) > 0 else "x"
    
    # Y轴
    if "y_axis" in requirements:
        config["y_axis"] = requirements["y_axis"]
    elif numeric_cols:
        config["y_axis"] = numeric_cols[0]
    else:
        config["y_axis"] = "value"
    
    # 是否平滑曲线
    config["smooth"] = True
    
    if "x_axis" in config and "y_axis" in config:
        config["title"] = f"{config['y_axis']} 趋势图"
    
    return config

def _generate_pie_chart_config(df, requirements, numeric_cols, categorical_cols):
    """生成饼图配置"""
    config = {"chart_type": "pie_chart"}
    
    # 饼图需要名称列和值列
    if categorical_cols:
        config["name_col"] = categorical_cols[0]
    else:
        config["name_col"] = df.columns[0] if len(df.columns) > 0 else "category"
    
    if numeric_cols:
        config["value_col"] = numeric_cols[0]
    else:
        # 如果没有数值列，使用计数
        config["value_col"] = "count"
    
    # 限制数据数量（饼图不宜过多分类）
    config["limit"] = 10
    
    config["title"] = f"{config['name_col']} 分布"
    
    return config

def _generate_scatter_chart_config(df, requirements, numeric_cols, categorical_cols):
    """生成散点图配置"""
    config = {"chart_type": "scatter_chart"}
    
    # 散点图需要两个数值轴
    if len(numeric_cols) >= 2:
        config["x_axis"] = numeric_cols[0]
        config["y_axis"] = numeric_cols[1]
    elif numeric_cols:
        config["x_axis"] = numeric_cols[0]
        config["y_axis"] = numeric_cols[0]
    else:
        config["x_axis"] = df.columns[0] if len(df.columns) > 0 else "x"
        config["y_axis"] = df.columns[1] if len(df.columns) > 1 else df.columns[0]
    
    # 如果有分类列，可以用作颜色或形状
    if categorical_cols and len(categorical_cols) > 0:
        config["color_by"] = categorical_cols[0]
    
    config["title"] = f"{config['y_axis']} 与 {config['x_axis']} 关系"
    
    return config

def _get_chart_by_requirements(df, requirements, numeric_cols, categorical_cols, datetime_cols):
    """根据用户要求选择图表"""
    
    # 检查用户要求特征
    has_x_axis = "x_axis" in requirements
    has_y_axis = "y_axis" in requirements
    has_limit = "limit" in requirements
    
    # 判断逻辑
    if has_x_axis and has_y_axis:
        # 如果有两个轴，可能是散点图或折线图
        if datetime_cols and requirements.get("x_axis") in datetime_cols:
            return _generate_line_chart_config(df, requirements, numeric_cols, categorical_cols, datetime_cols)
        else:
            return _generate_scatter_chart_config(df, requirements, numeric_cols, categorical_cols)
    
    elif has_x_axis or has_y_axis:
        # 只有一个轴，可能是柱状图
        return _generate_bar_chart_config(df, requirements, numeric_cols, categorical_cols)
    
    elif has_limit and len(categorical_cols) > 0:
        # 有数量限制和分类数据，适合饼图
        return _generate_pie_chart_config(df, requirements, numeric_cols, categorical_cols)
    
    else:
        # 默认智能推荐
        return _get_smart_chart_config(df, "", numeric_cols, categorical_cols, datetime_cols)

def _get_smart_chart_config(df, sql, numeric_cols, categorical_cols, datetime_cols):
    """智能图表推荐"""
    sql_lower = sql.lower()
    
    # 规则1: 分组统计查询 -> 柱状图
    if "group by" in sql_lower or "count(" in sql_lower:
        x_axis = categorical_cols[0] if categorical_cols else df.columns[0]
        y_axis = numeric_cols[0] if numeric_cols else df.columns[1] if len(df.columns) > 1 else df.columns[0]
        
        return {
            "chart_type": "bar_chart",
            "x_axis": x_axis,
            "y_axis": y_axis,
            "title": f"{y_axis} 按 {x_axis} 统计",
            "chart_style": "group_by"
        }
    
    # 规则2: 有数值列，并且行数适中 -> 柱状图
    elif numeric_cols and len(df) <= 20:
        x_axis = categorical_cols[0] if categorical_cols else df.columns[0]
        y_axis = numeric_cols[0]
        
        return {
            "chart_type": "bar_chart",
            "x_axis": x_axis,
            "y_axis": y_axis,
            "title": f"{y_axis} 统计",
            "chart_style": "simple_bar"
        }
    
    # 规则3: 多个数值列 -> 多系列柱状图
    elif len(numeric_cols) >= 2 and len(df) <= 15:
        return {
            "chart_type": "multi_bar_chart",
            "x_axis": categorical_cols[0] if categorical_cols else df.columns[0],
            "y_axes": numeric_cols[:3],
            "title": "多维度数据对比",
            "chart_style": "multi_series"
        }
    
    # 规则4: 只有分类数据 -> 饼图
    elif categorical_cols and not numeric_cols and len(df) <= 10:
        return {
            "chart_type": "pie_chart",
            "name_col": categorical_cols[0],
            "value_col": categorical_cols[1] if len(categorical_cols) > 1 else categorical_cols[0],
            "title": f"{categorical_cols[0]} 分布",
            "chart_style": "distribution"
        }
    
    # 规则5: 有时间序列数据 -> 折线图
    elif datetime_cols and numeric_cols:
        return {
            "chart_type": "line_chart",
            "x_axis": datetime_cols[0],
            "y_axis": numeric_cols[0],
            "title": f"{numeric_cols[0]} 趋势",
            "smooth": True,
            "chart_style": "time_series"
        }
    
    # 默认：表格
    else:
        return {
            "chart_type": "table",
            "show_table": True,
            "message": "数据量较大，建议使用表格查看"
        }