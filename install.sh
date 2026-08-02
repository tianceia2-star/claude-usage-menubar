#!/bin/bash
# 安裝 Claude 用量選單列小工具，並設定開機自動啟動（macOS LaunchAgent）。
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LABEL="com.claude-usage-widget.app"
PLIST_PATH="$HOME/Library/LaunchAgents/${LABEL}.plist"
PYTHON_BIN="$(command -v python3)"

if [ -z "$PYTHON_BIN" ]; then
  echo "找不到 python3，請先安裝 Python 3。" >&2
  exit 1
fi

echo "安裝相依套件..."
"$PYTHON_BIN" -m pip install --user -r "$REPO_DIR/requirements.txt"

echo "產生 LaunchAgent 設定：$PLIST_PATH"
mkdir -p "$HOME/Library/LaunchAgents"
cat > "$PLIST_PATH" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>Label</key>
	<string>${LABEL}</string>
	<key>ProgramArguments</key>
	<array>
		<string>${PYTHON_BIN}</string>
		<string>${REPO_DIR}/menu_bar_app.py</string>
	</array>
	<key>WorkingDirectory</key>
	<string>${REPO_DIR}</string>
	<key>RunAtLoad</key>
	<true/>
	<key>KeepAlive</key>
	<dict>
		<key>SuccessfulExit</key>
		<false/>
	</dict>
	<key>StandardOutPath</key>
	<string>${REPO_DIR}/menubar.log</string>
	<key>StandardErrorPath</key>
	<string>${REPO_DIR}/menubar.err.log</string>
</dict>
</plist>
EOF

UID_NUM="$(id -u)"
launchctl bootout "gui/${UID_NUM}/${LABEL}" >/dev/null 2>&1 || true
launchctl bootstrap "gui/${UID_NUM}" "$PLIST_PATH"

echo "完成！選單列應該已經出現 Claude 用量圖示。"
echo "完整面板：http://127.0.0.1:8765"
echo "解除安裝請跑：./uninstall.sh"
