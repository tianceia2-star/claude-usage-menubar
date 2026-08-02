# Claude Usage Menu Bar Widget

一個 macOS 選單列小工具，即時顯示 Claude Code 的 **5 小時 session 用量** 與 **7 天 weekly 用量**，以及各自的重置倒數。

![menu bar](assets/menubar_title.png)

點選單列圖示會展開更多細節（session/weekly 百分比與重置時間、最後更新時間），也可以「開啟完整面板」叫出網頁版做更大的顯示。

## ⚠️ 使用前必讀：這是非官方做法

這個小工具**不是**用 Anthropic 公開文件裡的官方 API，而是：

1. 呼叫 `/api/oauth/usage`——這是 Claude Code CLI 內建 `/status` 指令背後打的**同一個未公開端點**，回傳 session/weekly 用量百分比與重置時間。
2. 讀取 Claude Code 已經存在你 macOS 鑰匙圈（Keychain，服務名稱 `Claude Code-credentials`）裡的 OAuth token 來認證。
3. token 過期時，**不會**自己實作 OAuth refresh、也**不會**寫回鑰匙圈——而是跑一次極小的 `claude -p` headless 呼叫，借用 Claude Code CLI 自己既有、受信任的 token 刷新邏輯。這樣可以避免任何第三方程式碼直接竄改你的登入憑證，但也表示每次刷新會消耗你帳號極少量的用量額度。

這代表：
- **這不是 Anthropic 官方支援的功能**，端點隨時可能改版或關閉，屆時小工具會顯示「更新失敗」。
- 這個端點對頻繁輪詢的容忍度很低，所以本工具背景每 **5 分鐘**輪詢一次，手動按「立即更新」也有 **60 秒節流**保護，請不要修改成更頻繁的輪詢。
- 需要你已經用 `claude` CLI 登入過（`claude auth login`），且鑰匙圈裡能找到 `Claude Code-credentials`。

如果哪天這個端點失效了，這工具就會停止更新——這是使用非官方 API 的必然風險，使用前請自行評估。

## 需求

- macOS（用到 Keychain 與選單列 API，其他平台無法使用）
- Python 3
- 已安裝並登入過 [Claude Code](https://claude.com/claude-code) CLI（`claude auth login`）

## 安裝

```bash
git clone <this-repo-url>
cd claude-usage-widget
./install.sh
```

`install.sh` 會：
1. 安裝相依套件（[rumps](https://github.com/jaredks/rumps)，用來做選單列圖示）
2. 產生一份 macOS LaunchAgent（開機/登入自動啟動），寫到 `~/Library/LaunchAgents/`
3. 立即啟動小工具

啟動後選單列會出現用量圖示，網頁完整面板在 `http://127.0.0.1:8765`。

## 手動執行（不裝開機自動啟動）

```bash
pip3 install -r requirements.txt
python3 menu_bar_app.py
```

只想要網頁面板、不要選單列圖示的話：

```bash
python3 usage_server.py
```

## 解除安裝

```bash
./uninstall.sh
```

會移除 LaunchAgent 設定並停止小工具（不會動到你的 Claude Code 登入憑證）。

## 圖示顏色

- 🟢 用量 < 70%
- 🟡 用量 70–90%
- 🔴 用量 ≥ 90%

## 授權

MIT License，僅供個人使用，與 Anthropic 官方無關，使用本工具產生的任何用量消耗由使用者自行負責。
