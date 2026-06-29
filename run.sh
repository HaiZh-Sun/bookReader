#!/bin/bash
set -e

echo "=== BookReader 启动 ==="

# 后端
echo "[1/2] 启动后端 (FastAPI)..."
source backend/.venv/bin/activate
cd backend
uvicorn app:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# 等待后端就绪
sleep 2

# 前端
echo "[2/2] 启动前端 (Vite)..."
cd frontend
npx vite --host 0.0.0.0 &
FRONTEND_PID=$!
cd ..

echo ""
echo "后端: http://localhost:8000"
echo "前端: http://localhost:5173"
echo "API 文档: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
