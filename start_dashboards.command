#!/bin/bash

# ============================================
# Kakuleta Dashboard Launcher
# One-time startup script.
# Checks each dashboard, starts if not running,
# prints summary, then exits.
# ============================================

PROJECT_DIR="/Users/richarddaka/Documents/kakuleta_automation"

echo ""
echo "========================================"
echo "  Starting dashboards..."
echo "========================================"
echo ""

# Status variables (macOS bash 3.2 compatible)
STATUS_PORT3002="not running"
STATUS_PORT3003="not running"
STATUS_PORT3004="not running"
STATUS_PORT3005="not running"

check_and_start() {
  local port=$1
  local name=$2
  local dir=$3
  local url="http://localhost:$port"

  # Step 1: Check if already responding via curl
  local http_code
  http_code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 2 "$url" 2>/dev/null)

  if [ "$http_code" != "000" ]; then
    echo "  ✓ $name — Already running on port $port"
    eval "STATUS_PORT$port=\"running\""
    return
  fi

  # Step 2: Port occupied but not responding? Kill stale process
  if lsof -i :"$port" > /dev/null 2>&1; then
    echo "  ⚠ $name — Port $port is occupied but not responding. Killing stale process..."
    kill $(lsof -ti :"$port") 2>/dev/null
    sleep 1
  fi

  # Step 3: Start the dashboard (silently in background)
  echo "  → Starting $name on port $port..."
  cd "$dir" && python3 server.py > /dev/null 2>&1 &
  sleep 2

  # Step 4: Verify with curl
  http_code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 2 "$url" 2>/dev/null)
  if [ "$http_code" != "000" ]; then
    echo "  ✓ $name — Started successfully on port $port"
    eval "STATUS_PORT$port=\"running\""
  else
    echo "  ✗ $name — Failed to start on port $port"
    eval "STATUS_PORT$port=\"not running\""
  fi
}

# Start each dashboard (one-time, sequential)
check_and_start 3002 "Bond Dashboard"   "$PROJECT_DIR/bond-dashboard"
check_and_start 3003 "Dashboard 2"      "$PROJECT_DIR/tbill-dashboard"
check_and_start 3004 "Dashboard 3"      "$PROJECT_DIR/luse-dashboard"
check_and_start 3005 "Forex Dashboard"  "$PROJECT_DIR/forex-dashboard"

echo ""
echo "========================================"
echo "  Dashboard Status Summary"
echo "========================================"
echo "  port 3002 → $STATUS_PORT3002"
echo "  port 3003 → $STATUS_PORT3003"
echo "  port 3004 → $STATUS_PORT3004"
echo "  port 3005 → $STATUS_PORT3005"
echo "========================================"
echo ""
echo "  Opening launcher page..."
open "$PROJECT_DIR/launcher.html"
echo ""

# Keep terminal open so user can see the summary
read -p "  Press Enter to close this window..."
