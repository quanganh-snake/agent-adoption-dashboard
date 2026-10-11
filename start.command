#!/usr/bin/env bash

# Chuyển về thư mục chứa file start.command (thư mục dashboard)
cd "$(dirname "$0")" || exit 1

echo "=========================================================="
echo "  KHỞI ĐỘNG HỆ THỐNG AGENT ADOPTION DASHBOARD"
echo "=========================================================="

# Kiểm tra công cụ cần thiết
if ! command -v uv &> /dev/null; then
    echo "Lỗi: Không tìm thấy 'uv'. Hãy đảm bảo uv đã được cài đặt."
    read -p "Nhấn Enter để thoát..."
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "Lỗi: Không tìm thấy 'npm'. Hãy đảm bảo Node.js đã được cài đặt."
    read -p "Nhấn Enter để thoát..."
    exit 1
fi

# Hàm dọn dẹp khi nhấn Ctrl+C
cleanup() {
    echo ""
    echo "Đang dừng các dịch vụ..."
    if [ -n "$BACKEND_PID" ]; then
        kill "$BACKEND_PID" 2>/dev/null
    fi
    if [ -n "$FRONTEND_PID" ]; then
        kill "$FRONTEND_PID" 2>/dev/null
    fi
    wait 2>/dev/null
    echo "Đã dừng hoàn tất."
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# Giải phóng cổng 8000 và 3000 nếu có tiến trình cũ chiếm giữ
lsof -ti :8000 | xargs kill -9 2>/dev/null || true
lsof -ti :3000 | xargs kill -9 2>/dev/null || true

# 1. Khởi động Backend FastAPI
echo "[1/2] Đang khởi động Backend FastAPI (Port 8000)..."
cd backend || exit 1
uv run agentdash serve --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!
cd ..

# 2. Khởi động Frontend Next.js
echo "[2/2] Đang khởi động Frontend Next.js (Port 3000)..."
cd frontend || exit 1
# Dọn dẹp cache .next cũ trước khi dev để tránh lỗi 404 chunk
rm -rf .next 2>/dev/null || true
npm run dev -- -p 3000 &
FRONTEND_PID=$!
cd ..
# Chờ 3 giây rồi mở trình duyệt mặc định
(
    sleep 3
    if command -v open &> /dev/null; then
        open "http://localhost:3000"
    fi
) &

echo "----------------------------------------------------------"
echo "  Dashboard đang chạy tại:"
echo "  👉 Giao diện (Next.js):  http://localhost:3000"
echo "  👉 API (FastAPI):        http://localhost:8000"
echo "----------------------------------------------------------"
echo "  (Nhấn Ctrl+C trong cửa sổ này để tắt toàn bộ hệ thống)"
echo "----------------------------------------------------------"

# Giữ script chạy để theo dõi log
wait
