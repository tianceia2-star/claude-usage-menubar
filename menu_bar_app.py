#!/usr/bin/env python3
"""Claude 用量 macOS 選單列小工具。"""
import webbrowser
from datetime import datetime, timezone

import rumps
from AppKit import NSApplication, NSApplicationActivationPolicyAccessory

import usage_core
import http_server

# 隱藏 Dock 圖示與 Cmd+Tab 清單，只留選單列圖示。
NSApplication.sharedApplication().setActivationPolicy_(NSApplicationActivationPolicyAccessory)

DASHBOARD_URL = f"http://127.0.0.1:{http_server.PORT}"


def format_countdown(resets_at_iso):
    if not resets_at_iso:
        return "--"
    try:
        target = datetime.fromisoformat(resets_at_iso.replace("Z", "+00:00"))
    except Exception:
        return "--"
    diff = target - datetime.now(timezone.utc)
    total_seconds = max(0, int(diff.total_seconds()))
    days, rem = divmod(total_seconds, 86400)
    hours, rem = divmod(rem, 3600)
    mins, _ = divmod(rem, 60)
    if days > 0:
        return f"{days}天{hours}小時後重置"
    if hours > 0:
        return f"{hours}小時{mins}分後重置"
    return f"{mins}分後重置"


def format_countdown_compact(resets_at_iso):
    """給選單列標題用的簡短格式，例如 1hr 38min。"""
    if not resets_at_iso:
        return "--"
    try:
        target = datetime.fromisoformat(resets_at_iso.replace("Z", "+00:00"))
    except Exception:
        return "--"
    diff = target - datetime.now(timezone.utc)
    total_seconds = max(0, int(diff.total_seconds()))
    days, rem = divmod(total_seconds, 86400)
    hours, rem = divmod(rem, 3600)
    mins, _ = divmod(rem, 60)
    if days > 0:
        return f"{days}d {hours}hr"
    if hours > 0:
        return f"{hours}hr {mins}min"
    return f"{mins}min"


def status_emoji(pct):
    if pct is None:
        return "⚪"
    if pct >= 90:
        return "🔴"
    if pct >= 70:
        return "🟡"
    return "🟢"


class UsageApp(rumps.App):
    def __init__(self):
        super().__init__("Claude用量", title="⚪ --%", quit_button="結束")
        self.session_item = rumps.MenuItem("Session: --")
        self.weekly_item = rumps.MenuItem("Weekly: --")
        self.updated_item = rumps.MenuItem("尚未更新")
        self.menu = [
            self.session_item,
            self.weekly_item,
            rumps.separator,
            rumps.MenuItem("立即更新", callback=self.manual_refresh),
            rumps.MenuItem("開啟完整面板", callback=self.open_dashboard),
            rumps.separator,
            self.updated_item,
        ]
        self.refresh_display()

    def open_dashboard(self, _sender):
        webbrowser.open(DASHBOARD_URL)

    def manual_refresh(self, _sender):
        usage_core.refresh_state(force=False)
        self.refresh_display()

    @rumps.timer(20)
    def tick(self, _sender):
        self.refresh_display()

    def refresh_display(self):
        snap = usage_core.get_state_snapshot()
        data = snap.get("data")
        if not data:
            self.title = "⚪ --%"
            if snap.get("error"):
                self.updated_item.title = f"更新失敗：{snap['error']}"
            return

        five_hour = data.get("five_hour", {})
        seven_day = data.get("seven_day", {})
        s_pct = five_hour.get("utilization")
        w_pct = seven_day.get("utilization")

        if s_pct is not None:
            remaining = format_countdown_compact(five_hour.get("resets_at"))
            self.title = f"{status_emoji(s_pct)} {int(s_pct)}% ({remaining}⏳)"
        else:
            self.title = "⚪ --%"
        self.session_item.title = (
            f"Session: {int(s_pct)}%・{format_countdown(five_hour.get('resets_at'))}"
            if s_pct is not None else "Session: --"
        )
        self.weekly_item.title = (
            f"Weekly: {int(w_pct)}%・{format_countdown(seven_day.get('resets_at'))}"
            if w_pct is not None else "Weekly: --"
        )
        fetched_at = snap.get("fetched_at")
        if fetched_at:
            t = datetime.fromtimestamp(fetched_at).strftime("%H:%M:%S")
            suffix = f"（{snap['error']}）" if snap.get("error") else ""
            self.updated_item.title = f"最後更新 {t}{suffix}"
        else:
            self.updated_item.title = "尚未更新"


def main():
    usage_core.start_poll_thread()
    http_server.start_server_thread()
    UsageApp().run()


if __name__ == "__main__":
    main()
