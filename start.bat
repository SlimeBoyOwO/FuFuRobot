@echo off
REM 强制设置 CMD 使用 UTF-8 代码页
chcp 65001 > nul

REM =======================================================
echo.
echo =======================================================
echo 启动脚本：芙芙
echo =======================================================

set "BASE_DIR=%~dp0"

echo.
echo [1/4] 检查Python环境...

python --version >nul 2>&1
if ERRORLEVEL 1 (
    echo ❌ 错误: 未找到Python，请先安装Python 3.7+
    pause
    exit /b 1
)

echo.
echo [2/4] 激活虚拟环境...

if exist "%BASE_DIR%.venv\Scripts\activate.bat" (
    call "%BASE_DIR%.venv\Scripts\activate.bat"
    echo ✅ 虚拟环境激活成功
) else (
    echo ⚠️ 使用系统Python
)

echo.
echo [3/4] 检查依赖...

python -c "import fastapi, uvicorn" 2>nul
if ERRORLEVEL 1 (
    echo ⚠️ 正在安装依赖...
    pip install fastapi uvicorn python-dotenv pandas aiofiles --quiet
    echo ✅ 依赖安装完成
)

echo.
echo [4/4] 启动前后端服务...

REM 检查端口占用
netstat -ano | findstr ":8000 " >nul && (
    echo ⚠️ 端口8000被占用，尝试清理...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000 "') do taskkill /F /PID %%a >nul 2>&1
)

netstat -ano | findstr ":8080 " >nul && (
    echo ⚠️ 端口8080被占用，尝试清理...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8080 "') do taskkill /F /PID %%a >nul 2>&1
)

echo.
echo 🚀 启动后端API服务 (端口 8000)...
start "AI学生管理系统 - 后端API" cmd /k "chcp 65001 > nul && echo [后端API] 正在启动... && cd /d "%BASE_DIR%" && python main.py"

timeout /t 6 /nobreak > nul

echo 🚀 启动前端API服务 (端口 8080)...
start "AI学生管理系统 - 前端API" cmd /k "chcp 65001 > nul && echo [前端API] 正在启动... && cd /d "%BASE_DIR%" && python frontend_server.py"
echo.
echo 🌐 正在打开浏览器...
start "" "http://127.0.0.1:8080/"

echo.
echo =======================================================
echo ✅ 系统启动完成！
echo =======================================================
echo.
echo 📡 服务信息:
echo    前端界面: http://127.0.0.1:8080/
echo    后端API: http://127.0.0.1:8000/
echo    API文档: http://127.0.0.1:8000/docs
echo.
echo 🔧 技术架构:
echo    • 前端: HTML/CSS/JavaScript (ES6模块化)
echo    • 前端服务器: FastAPI静态文件服务 (端口8080)
echo    • 后端API: FastAPI REST API (端口8000)
echo.
echo 💡 提示:
echo    • 前端调用后端API地址: http://127.0.0.1:8000/api
echo    • 要使用DeepSeek API，请编辑 backend/.env 文件
echo    • 按 Ctrl+C 停止各服务
echo =======================================================
echo.
echo 按任意键退出此窗口...
pause >nul