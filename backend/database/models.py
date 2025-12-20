# backend/database/models.py
import sqlite3
from typing import Dict, Any

def init_db():
    """初始化数据库，创建表并插入测试数据"""
    try:
        with sqlite3.connect('students.db') as conn:
            cursor = conn.cursor()
            
            # 创建学生表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    student_id TEXT UNIQUE NOT NULL,
                    class_name TEXT,
                    college TEXT,
                    major TEXT,
                    grade TEXT,
                    gender TEXT CHECK(gender IN ('男', '女')),
                    phone TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_college ON students(college)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_major ON students(major)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_grade ON students(grade)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_gender ON students(gender)')
            
            # 插入一些测试数据（如果表是空的）
            cursor.execute("SELECT count(*) FROM students")
            if cursor.fetchone()[0] == 0:
                data = [
                    ('张三', '2023001', '一班', '计算机学院', '软件工程', '2023级', '男', '13800138001'),
                    ('李四', '2023002', '二班', '经管学院', '会计学', '2023级', '女', '13800138002'),
                    ('王五', '2023003', '一班', '计算机学院', '软件工程', '2023级', '男', '13800138003'),
                    ('赵六', '2022004', '三班', '计算机学院', '计算机科学', '2022级', '女', '13800138004'),
                    ('钱七', '2023005', '二班', '文学院', '汉语言文学', '2023级', '男', '13800138005'),
                    ('孙八', '2022006', '一班', '理学院', '数学与应用数学', '2022级', '女', '13800138006'),
                    ('周九', '2023007', '三班', '计算机学院', '软件工程', '2023级', '男', '13800138007'),
                    ('吴十', '2022008', '二班', '经管学院', '金融学', '2022级', '女', '13800138008'),
                    ('郑十一', '2023009', '一班', '医学院', '临床医学', '2024级', '女', '13800138009'),
                    ('王十二', '2023010', '三班', '理学院', '应用化学', '2024级', '男', '13800138010'),
                    ('冯十三', '2023011', '二班', '文学院', '新闻学', '2024级', '女', '13800138011'),
                    ('陈十四', '2022012', '一班', '经管学院', '财务管理', '2022级', '男', '13800138012'),
                    ('褚十五', '2023013', '三班', '计算机学院', '人工智能', '2024级', '男', '13800138013'),
                    ('卫十六', '2022014', '二班', '医学院', '护理学', '2022级', '女', '13800138014'),
                    ('蒋十七', '2023015', '一班', '理学院', '物理学', '2023级', '男', '13800138015'),
                    ('沈十八', '2022016', '三班', '文学院', '广告学', '2022级', '女', '13800138016'),
                    ('韩十九', '2023017', '二班', '经管学院', '国际经济与贸易', '2024级', '男', '13800138017'),
                    ('杨二十', '2022018', '一班', '计算机学院', '信息安全', '2022级', '女', '13800138018'),
                    ('朱二一', '2023019', '三班', '医学院', '口腔医学', '2023级', '男', '13800138019'),
                    ('秦二二', '2023020', '二班', '理学院', '统计学', '2024级', '女', '13800138020'),
                    ('尤二三', '2023021', '一班', '文学院', '历史学', '2023级', '男', '13800138021'),
                    ('许二四', '2023022', '三班', '经管学院', '人力资源管理', '2023级', '女', '13800138022'),
                    ('何二五', '2023023', '二班', '计算机学院', '物联网工程', '2024级', '男', '13800138023'),
                    ('吕二六', '2022024', '一班', '医学院', '药学', '2022级', '女', '13800138024'),
                    ('施二七', '2022025', '三班', '理学院', '化学工程与工艺', '2022级', '男', '13800138025'),
                    ('张二八', '2023026', '二班', '文学院', '秘书学', '2024级', '女', '13800138026'),
                    ('孔二九', '2022027', '一班', '经管学院', '市场营销', '2022级', '男', '13800138027'),
                    ('曹三十', '2023028', '三班', '计算机学院', '数据科学与大数据技术', '2023级', '女', '13800138028'),
                    ('严三一', '2023029', '二班', '医学院', '康复治疗学', '2024级', '男', '13800138029'),
                    ('华三二', '2023030', '一班', '理学院', '地理科学', '2023级', '女', '13800138030'),
                ]
                cursor.executemany('''
                    INSERT INTO students (name, student_id, class_name, college, major, grade, gender, phone) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', data)
                conn.commit()
                print("数据库初始化完成，已插入30条测试数据。")
            else:
                print("数据库已存在，跳过数据插入。")
            
    except Exception as e:
        print(f"数据库初始化失败: {e}")

def get_table_info() -> Dict[str, Any]:
    """获取表结构信息"""
    try:
        with sqlite3.connect('students.db') as conn:
            cursor = conn.cursor()
            
            # 获取students表的结构
            cursor.execute("PRAGMA table_info(students)")
            columns_info = cursor.fetchall()
            
            # 获取数据统计
            cursor.execute("SELECT COUNT(*) FROM students")
            total_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT college, COUNT(*) FROM students GROUP BY college")
            college_stats = cursor.fetchall()
            
            # 获取所有数据示例（前5条）
            cursor.execute("SELECT * FROM students LIMIT 5")
            sample_data = cursor.fetchall()
            
            return {
                "columns": columns_info,
                "total_count": total_count,
                "college_stats": college_stats,
                "sample_data": sample_data
            }
    except Exception as e:
        return {"error": str(e)}