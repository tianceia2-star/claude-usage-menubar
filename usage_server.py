#!/usr/bin/env python3
"""純網頁版入口（不含選單列圖示）。要選單列圖示請改跑 menu_bar_app.py。"""
import usage_core
import http_server


def main():
    usage_core.start_poll_thread()
    http_server.start_server_thread()
    print(f"Claude 用量面板: http://127.0.0.1:{http_server.PORT}")
    import time
    while True:
        time.sleep(3600)


if __name__ == "__main__":
    main()
