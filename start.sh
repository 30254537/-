#!/usr/bin/env bash
# ============================================================================
#  MixMind DJ — one-click launcher for macOS / Linux
#  Sets up venv, installs deps, seeds demo, starts API + frontend.
# ============================================================================
set -e

# Resolve the directory containing this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
G='\033[0;32m'   # green
B='\033[0;34m'   # blue
Y='\033[1;33m'   # yellow
R='\033[0;31m'   # red
N='\033[0m'      # reset

echo
echo -e "${B}=====================================================${N}"
echo -e "${B} MixMind DJ — Starting${N}"
echo -e "${B}=====================================================${N}"
echo

# Pick a python binary
PYTHON=""
for cand in python3.11 python3.12 python3.13 python3 python; do
  if command -v "$cand" >/dev/null 2>&1; then
    PYTHON="$cand"
    break
  fi
done
if [ -z "$PYTHON" ]; then
  echo -e "${R}ERROR: Python 3.11+ not found. Install from https://www.python.org/${N}"
  exit 1
fi
echo -e "Using Python: $($PYTHON --version)"

# 1. venv
if [ ! -d backend/venv ]; then
  echo -e "${G}[1/5]${N} Creating Python virtual environment..."
  "$PYTHON" -m venv backend/venv
else
  echo -e "${G}[1/5]${N} Backend venv already exists"
fi

# 2. install deps
echo -e "${G}[2/5]${N} Installing Python dependencies..."
# shellcheck disable=SC1091
source backend/venv/bin/activate
pip install --upgrade pip --quiet
pip install -r backend/requirements.txt --quiet

# 3. health check
echo -e "${G}[3/5]${N} Running health check..."
(cd backend && python -m mixmind health) || {
  echo -e "${R}Health check failed.${N}"
  exit 1
}

# 4. frontend deps
echo -e "${G}[4/5]${N} Installing frontend dependencies..."
if ! command -v npm >/dev/null 2>&1; then
  echo -e "${R}ERROR: npm not found. Install Node.js 20+ from https://nodejs.org/${N}"
  exit 1
fi
if [ ! -d frontend/node_modules ]; then
  (cd frontend && npm install)
else
  echo "Frontend node_modules already present"
fi

# 5. seed demo if library empty
TRACKS=$(cd backend && python -m mixmind stats 2>/dev/null | grep -oE 'Total tracks: [0-9]+' | grep -oE '[0-9]+' || echo "0")
if [ "$TRACKS" = "0" ]; then
  echo -e "${G}[5/5]${N} Library is empty — seeding 60 demo tracks..."
  (cd backend && python -m mixmind demo)
else
  echo -e "${G}[5/5]${N} Library has $TRACKS tracks already"
fi

echo
echo -e "${B}=====================================================${N}"
echo -e "${B} Launching MixMind DJ${N}"
echo -e "${B} Backend: http://127.0.0.1:8000${N}"
echo -e "${B} Web UI:  http://localhost:5173${N}"
echo -e "${B}=====================================================${N}"
echo

# Trap Ctrl-C to clean up both processes
cleanup() {
  echo
  echo -e "${Y}Shutting down...${N}"
  [ -n "$BACKEND_PID" ] && kill "$BACKEND_PID" 2>/dev/null || true
  [ -n "$FRONTEND_PID" ] && kill "$FRONTEND_PID" 2>/dev/null || true
  exit 0
}
trap cleanup INT TERM

# Start backend
(cd backend && uvicorn mixmind.api:app --reload) &
BACKEND_PID=$!

# Wait for backend to be ready
echo "Waiting for backend..."
for i in 1 2 3 4 5 6 7 8 9 10; do
  if curl -s http://127.0.0.1:8000/api/health >/dev/null 2>&1; then
    echo -e "${G}Backend up.${N}"
    break
  fi
  sleep 1
done

# Start frontend
(cd frontend && npm run dev) &
FRONTEND_PID=$!

# Open browser (best effort)
sleep 4
if command -v open >/dev/null 2>&1; then
  open http://localhost:5173
elif command -v xdg-open >/dev/null 2>&1; then
  xdg-open http://localhost:5173 >/dev/null 2>&1 &
fi

echo
echo -e "${Y}Press Ctrl+C to stop both servers.${N}"
wait
