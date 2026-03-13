#!/bin/bash

echo "========================================"
echo "PDF 笔记生成器 - 快速启动脚本"
echo "========================================"
echo

echo "[1/3] 检查后端环境..."
cd backend
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 Python3"
    echo "请先安装 Python 3.8+"
    exit 1
fi

echo "[2/3] 检查依赖..."
if [ ! -f ".env" ]; then
    echo
    echo "首次运行，需要配置环境变量..."
    cp .env.example .env
    echo
    echo "========================================"
    echo "重要：请编辑 backend/.env 文件"
    echo "设置 DASHSCOPE_API_KEY"
    echo "========================================"
    echo
    echo "配置完成后，请重新运行此脚本"
    exit 0
fi

echo "[3/3] 启动后端服务..."
echo
echo "后端将在 http://localhost:8000 启动"
echo "按 Ctrl+C 停止服务"
echo
python3 main.py