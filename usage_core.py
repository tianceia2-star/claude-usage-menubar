"""共用核心：讀鑰匙圈、呼叫 Anthropic 用量端點、背景輪詢、快取。

被 usage_server.py（純網頁版）與 menu_bar_app.py（選單列版）共用，
避免兩邊各刻一份一樣的邏輯。
"""
import json
import shutil
import subprocess
import threading
import time
import urllib.request
from pathlib import Path

POLL_INTERVAL_SECONDS = 300  # 背景自動輪詢間隔（5 分鐘）
MIN_REFRESH_INTERVAL_SECONDS = 60  # 手動更新的最短間隔，避免打太兇被端點擋
KEYCHAIN_SERVICE = "Claude Code-credentials"
USAGE_ENDPOINT = "https://api.anthropic.com/api/oauth/usage"

BASE_DIR = Path(__file__).resolve().parent
CACHE_FILE = BASE_DIR / ".usage_cache.json"

# launchd 背景執行時 PATH 很陽春（只有 /usr/bin:/bin:/usr/sbin:/sbin），
# 找不到裝在 ~/.local/bin 的 claude，所以優先找得到就用 which，找不到就退回已知安裝路徑。
CLAUDE_BIN = shutil.which("claude") or str(Path.home() / ".local" / "bin" / "claude")

state_lock = threading.Lock()
state = {
    "data": None,
    "fetched_at": None,
    "error": None,
    "token_hint": None,
}


def load_cache():
    if CACHE_FILE.exists():
        try:
            cached = json.loads(CACHE_FILE.read_text())
            with state_lock:
                state["data"] = cached.get("data")
                state["fetched_at"] = cached.get("fetched_at")
        except Exception:
            pass


def save_cache():
    with state_lock:
        snapshot = {"data": state["data"], "fetched_at": state["fetched_at"]}
    try:
        CACHE_FILE.write_text(json.dumps(snapshot))
    except Exception:
        pass


def read_keychain_credentials():
    result = subprocess.run(
        ["security", "find-generic-password", "-s", KEYCHAIN_SERVICE, "-w"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        raise RuntimeError("讀取鑰匙圈失敗，請確認已用 `claude` 登入過")
    return json.loads(result.stdout)["claudeAiOauth"]


def is_expired(creds, buffer_seconds=60):
    expires_at_ms = creds.get("expiresAt", 0)
    now_ms = time.time() * 1000
    return now_ms >= (expires_at_ms - buffer_seconds * 1000)


def trigger_cli_refresh():
    """跑一次極小的 headless 呼叫，讓 claude CLI 用它自己的邏輯刷新 token。"""
    subprocess.run(
        [CLAUDE_BIN, "-p", ".", "--model", "haiku", "--max-turns", "1"],
        capture_output=True,
        text=True,
        timeout=60,
        cwd="/tmp",
    )


def get_valid_access_token():
    creds = read_keychain_credentials()
    if is_expired(creds):
        trigger_cli_refresh()
        creds = read_keychain_credentials()
    token = creds["accessToken"]
    if not token:
        raise RuntimeError(
            "OAuth session 已失效且無法自動刷新，請重新用 `claude` 登入一次"
        )
    # 記錄目前鑰匙圈裡是哪個 token（只留末 6 碼），用來判斷切換帳號後
    # 鑰匙圈是否真的換成新帳號，而不是還在讀到舊的殘留 token。
    with state_lock:
        state["token_hint"] = token[-6:]
    return token


def fetch_usage():
    token = get_valid_access_token()
    req = urllib.request.Request(
        USAGE_ENDPOINT,
        headers={
            "Authorization": f"Bearer {token}",
            "anthropic-beta": "oauth-2025-04-20",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def refresh_state(force=False):
    with state_lock:
        last = state["fetched_at"]
    if not force and last:
        elapsed = time.time() - last
        if elapsed < MIN_REFRESH_INTERVAL_SECONDS:
            return
    try:
        data = fetch_usage()
        with state_lock:
            state["data"] = data
            state["fetched_at"] = time.time()
            state["error"] = None
    except Exception as e:
        with state_lock:
            state["error"] = str(e)
    save_cache()


def get_state_snapshot():
    with state_lock:
        return {
            "data": state["data"],
            "fetched_at": state["fetched_at"],
            "error": state["error"],
            "token_hint": state["token_hint"],
        }


def start_poll_thread():
    def poll_loop():
        while True:
            refresh_state(force=True)
            time.sleep(POLL_INTERVAL_SECONDS)

    load_cache()
    t = threading.Thread(target=poll_loop, daemon=True)
    t.start()
    return t
