# backend/frontend_server.py
"""
专门为前端提供静态文件服务的FastAPI应用
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# 修复 Windows 控制台编码问题
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

try:
    from backend.config import FRONTEND_HOST, FRONTEND_PORT, BASE_DIR
except ImportError:
    print("错误: 无法导入配置模块。请确保 backend/config.py 存在且可访问。")
    sys.exit(1)

# 获取前端目录
FRONTEND_SOURCE_DIR = BASE_DIR/ "frontend"

print("=" * 60)
print("前端静态文件服务")
print("=" * 60)

# 检查前端目录
if not FRONTEND_SOURCE_DIR.exists():
    print(f"错误: 找不到前端目录: {FRONTEND_SOURCE_DIR}")
    print("请确保 frontend/ 目录存在并包含以下文件:")
    print("   frontend/index.html")
    print("   frontend/css/style.css")
    print("   frontend/js/ 目录")
    sys.exit(1)

print(f"前端目录: {FRONTEND_SOURCE_DIR}")

# 创建FastAPI应用
app = FastAPI(
    title="前端静态文件服务",
    description="提供HTML、CSS、JS等静态文件",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 主页路由
@app.get("/", response_class=HTMLResponse)
async def serve_home():
    """提供首页"""
    index_path = FRONTEND_SOURCE_DIR / "index.html"
    if index_path.exists():
        # 读取并修改HTML文件中的API路径
        with open(index_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        return HTMLResponse(content=html_content, status_code=200)
    else:
        return HTMLResponse(
            content=f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>前端服务</title>
                <style>
                    body {{ font-family: Arial, sans-serif; padding: 50px; text-align: center; }}
                    .error {{ color: #e74c3c; background: #fdeaea; padding: 20px; border-radius: 5px; margin: 20px auto; max-width: 600px; }}
                </style>
            </head>
            <body>
                <h1>前端静态文件服务</h1>
                <div class="error">
                    <p>index.html 文件未找到</p>
                    <p>请确保 frontend/index.html 存在于以下路径:</p>
                    <p><code>{FRONTEND_SOURCE_DIR}</code></p>
                </div>
            </body>
            </html>
            """,
            status_code=200
        )

# 健康检查
@app.get("/health")
async def health_check():
    """健康检查"""
    js_files = list((FRONTEND_SOURCE_DIR / "js").glob("*.js")) if (FRONTEND_SOURCE_DIR / "js").exists() else []
    
    return {
        "status": "healthy",
        "service": "frontend-static-server",
        "port": FRONTEND_PORT,
        "directory": str(FRONTEND_SOURCE_DIR),
        "files": {
            "index.html": (FRONTEND_SOURCE_DIR / "index.html").exists(),
            "style.css": (FRONTEND_SOURCE_DIR / "css" / "style.css").exists(),
            "js_files": len(js_files),
            "js_file_list": [f.name for f in js_files]
        }
    }

# 挂载静态文件
@app.on_event("startup")
async def mount_static_files():
    """挂载静态文件目录"""
    try:
        # 挂载CSS文件
        if (FRONTEND_SOURCE_DIR / "css").exists():
            app.mount("/css", StaticFiles(directory=str(FRONTEND_SOURCE_DIR / "css")), name="css")
            print(f"CSS文件目录已挂载: {FRONTEND_SOURCE_DIR / 'css'}")
        
        # 挂载JS文件
        if (FRONTEND_SOURCE_DIR / "js").exists():
            app.mount("/js", StaticFiles(directory=str(FRONTEND_SOURCE_DIR / "js")), name="js")
            print(f"JS文件目录已挂载: {FRONTEND_SOURCE_DIR / 'js'}")
        
        # 挂载其他静态文件（图片等）
        if (FRONTEND_SOURCE_DIR/"images").exists():
            app.mount("/images", StaticFiles(directory=str(FRONTEND_SOURCE_DIR/"images")), name="images")
            print(f"图片文件目录已挂载: {FRONTEND_SOURCE_DIR/'images'}")
        
        print("所有静态文件服务已就绪")
        
    except Exception as e:
        print(f"挂载静态文件失败: {e}")

# 静态文件回退路由
@app.get("/{path:path}")
async def serve_static_file(path: str):
    """提供静态文件服务"""
    file_path = FRONTEND_SOURCE_DIR / path
    
    # 安全性检查：确保请求的文件在前端目录内
    try:
        file_path.relative_to(FRONTEND_SOURCE_DIR)
    except ValueError:
        return HTMLResponse(
            content=f"<h1>403 Forbidden</h1><p>Access to '{path}' is not allowed.</p>",
            status_code=403
        )
    
    if file_path.exists() and file_path.is_file():
        return FileResponse(file_path)
    else:
        return HTMLResponse(
            content=f"<h1>404 Not Found</h1><p>File '{path}' does not exist.</p>",
            status_code=404
        )

if __name__ == "__main__":
    print("启动前端服务器...")
    print(f"访问地址: http://{FRONTEND_HOST}:{FRONTEND_PORT}")
    print(f"API后端地址: http://127.0.0.1:8000")
    print("=" * 60)
    
    try:
        uvicorn.run(app, host=FRONTEND_HOST, port=FRONTEND_PORT)
    except Exception as e:
        print(f"服务器启动失败: {e}")
        import traceback
        traceback.print_exc()
        input("按 Enter 退出...")