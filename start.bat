@echo off
echo ========================================
echo PDF 笔记生成器 - 快速启动脚本
echo ========================================
echo.

echo [1/3] 检查后端环境...
cd backend
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Python
    echo 请先安装 Python 3.8+
    pause
    exit /b 1
)

echo [2/3] 检查依赖...
if not exist ".env" (
    echo.
    echo 首次运行，需要配置环境变量...
    copy .env.example .env >nul
    echo.
    echo ========================================
    echo 重要：请编辑 backend\.env 文件
    echo 设置 DASHSCOPE_API_KEY
    echo ========================================
    echo.
    notepad .env
    echo.
    echo 配置完成后，请重新运行此脚本
    pause
    exit /b 0
)

echo [3/3] 启动后端服务...
echo.
echo 后端将在 http://localhost:8000 启动
echo 按 Ctrl+C 停止服务
echo.
python main.py