# backend/main.py
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from backend.config import (
    APP_NAME, APP_VERSION, APP_DESCRIPTION,
    BACKEND_HOST, BACKEND_PORT
)
from backend.database import init_db, check_db_connection
from backend.api import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时的代码
    print("正在启动AI学生管理系统...")
    print("=" * 50)
    
    # 检查数据库连接
    db_status, db_message = check_db_connection()
    print(f"数据库状态: {db_message}")
    
    if db_status:
        init_db()
    else:
        print("警告: 数据库连接失败，请检查")
    
    # 检查DeepSeek API配置
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if api_key:
        masked_key = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
        print(f"DeepSeek API配置: 已设置 (密钥: {masked_key})")
    else:
        print("警告: DeepSeek API配置: 未设置 (将使用模拟模式)")
    
    print("=" * 50)
    yield
    # 关闭时的代码
    print("系统正在关闭...")

def create_app() -> FastAPI:
    """创建FastAPI应用"""
    app = FastAPI(
        title=APP_NAME,
        description=APP_DESCRIPTION,
        version=APP_VERSION,
        lifespan=lifespan
    )
    
    # 配置CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 包含API路由
    app.include_router(router)
    
    # 根路由
    @app.get("/")
    async def root():
        return {
            "message": f"{APP_NAME} API v{APP_VERSION}",
            "version": APP_VERSION,
            "status": "运行中",
            "features": [
                "智能对话 (DeepSeek API)",
                "智能SQL生成 (增删改查全支持)",
                "数据可视化",
                "数据库管理"
            ],
            "endpoints": {
                "chat": "/api/chat (POST)",
                "execute_sql": "/api/execute-sql (POST)",
                "clear_history": "/api/clear-history (POST)",
                "test_api": "/api/test-api (POST)",
                "health": "/api/health (GET)",
                "system_info": "/api/system-info (GET)",
                "db_info": "/api/db-info (GET)"
            },
            "docs": "/docs",
            "redoc": "/redoc"
        }
    
    return app

# 创建应用实例
app = create_app()

def main():
    print("=" * 50)
    print(f"{APP_NAME} v{APP_VERSION}")
    print(f"启动服务器: http://{BACKEND_HOST}:{BACKEND_PORT}")
    print(f"API文档: http://{BACKEND_HOST}:{BACKEND_PORT}/docs")
    print("现在等待6秒来启动前端服务器...")
    print("=" * 50)
    
    uvicorn.run(
        app, 
        host=BACKEND_HOST, 
        port=BACKEND_PORT,
        log_level="info"
    )

if __name__ == "__main__":
    main()