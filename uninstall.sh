#!/bin/bash
# 移除開機自動啟動設定並停止小工具。
set -euo pipefail

LABEL="com.claude-usage-widget.app"
PLIST_PATH="$HOME/Library/LaunchAgents/${LABEL}.plist"
UID_NUM="$(id -u)"

launchctl bootout "gui/${UID_NUM}/${LABEL}" >/dev/null 2>&1 || true
rm -f "$PLIST_PATH"
pkill -f "menu_bar_app.py" >/dev/null 2>&1 || true

echo "已移除開機自動啟動設定並停止小工具。"
