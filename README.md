# 🤖 Facebook Automation Bot v1.1.1

<div align="center">

**A production-ready Telegram-controlled Facebook Automation Bot with advanced anti-detect capabilities**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Telegram](https://img.shields.io/badge/Telegram-Bot%20API-blue.svg)](https://core.telegram.org/bots)
[![Selenium](https://img.shields.io/badge/Selenium-WebDriver-green.svg)](https://selenium.dev)
[![Chrome](https://img.shields.io/badge/Chrome-Extension%20Proxy-orange.svg)](https://developer.chrome.com/docs/extensions/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Project Structure](#-project-structure)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Telegram Commands](#-telegram-commands)
- [Anti-Detection Techniques](#-anti-detection-techniques)
- [Proxy Extension System](#-proxy-extension-system)
- [Account Management](#-account-management)
- [API Reference](#-api-reference)
- [Troubleshooting](#-troubleshooting)
- [Security Considerations](#-security-considerations)
- [Contributing](#-contributing)

---

## 🎯 Overview

This bot provides a seamless interface to automate Facebook operations through Telegram. Built with a focus on **stealth, reliability, and production-readiness**, it employs advanced anti-detection mechanisms to ensure stable, long-term automation without triggering Facebook's security systems.

### What's New in v1.1.1

- ✅ **Removed Selenium-Wire** - Eliminated MITM proxy that caused reCAPTCHA detection
- ✅ **Dynamic Chrome Extension Proxy** - MV3-compatible proxy authentication
- ✅ **Human-Assisted Manual Login** - Visible browser for secure credential entry
- ✅ **Auto-Save Cookies** - Automatic session persistence after successful operations
- ✅ **Warm-up Behavior** - Visits Facebook home before actions (human-like pattern)
- ✅ **Account Relogin Feature** - Fresh profile regeneration with new proxy
- ✅ **IP Kill Switch** - Automatic abort if proxy leaks real IP

### Tech Stack

| Technology                  | Purpose                              |
| --------------------------- | ------------------------------------ |
| **Python 3.8+**             | Core language                        |
| **Pyrogram / Pyrofork**     | Telegram Bot MTProto framework       |
| **undetected-chromedriver** | Anti-detect browser automation       |
| **Selenium WebDriver**      | Browser control                      |
| **Chrome Extension (MV3)**  | Dynamic proxy authentication         |
| **DataImpulse**             | Residential proxy network (optional) |

---

## ✨ Key Features

### 🛡️ Advanced Anti-Detection System

The bot uses a multi-layered anti-detection architecture:

| Layer        | Technology              | Purpose                                           |
| ------------ | ----------------------- | ------------------------------------------------- |
| **Browser**  | undetected-chromedriver | Patches Chrome to evade WebDriver detection       |
| **Proxy**    | Chrome Extension (MV3)  | Native proxy auth without MITM (avoids reCAPTCHA) |
| **Behavior** | Warm-up visits          | Visits Facebook home before actions               |
| **Sessions** | Profile isolation       | Each account has dedicated browser profile        |
| **Cookies**  | Auto-save               | Keeps sessions fresh with renewed tokens          |

### 🌐 Smart Proxy Management

**Dynamic Chrome Extension Generation:**

Instead of using Selenium-Wire (which Facebook detects), the bot dynamically generates a Chrome extension for each proxy configuration:

```python
# Automatically creates MV3 extension with embedded credentials
proxy_extension = create_proxy_extension(
    host="gw.dataimpulse.com",
    port=823,
    username="user__sessid.abc123",
    password="password"
)
```

**Features:**

- ✅ No MITM proxy (undetectable)
- ✅ MV3 compatible (Chrome 108+)
- ✅ Async auth handling
- ✅ Sticky sessions per account

### 📁 Profile Isolation

Each Facebook account operates in complete isolation:

```
profiles/
├── user1_example_com/
│   ├── Default/
│   │   ├── Cookies
│   │   ├── Local Storage/
│   │   └── Session Storage/
│   └── Local State
└── user2_example_com/
    └── ...
```

### 🍪 Automatic Cookie Management

- **Auto-save after success**: Cookies saved automatically after react/comment/share/follow
- **Session persistence**: Tokens renewed to prevent expiration
- **Path tracking**: `cookies/{email}.json` per account

### 🏠 Human-Like Warm-up Behavior

Before performing any action, the bot:

1. Opens a new browser tab
2. Visits `facebook.com` home feed
3. Pauses 2-4 seconds (randomized)
4. Navigates to target post/page

This mimics natural user behavior and reduces detection risk.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        TELEGRAM LAYER                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   /start    │  │   /login    │  │  /services  │              │
│  │   Handler   │  │   Handler   │  │   Handler   │              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
│         └────────────────┼────────────────┘                     │
│                          ▼                                      │
│                 ┌─────────────────┐                             │
│                 │  FacebookUtils  │  ← Orchestration Layer      │
│                 └────────┬────────┘                             │
└──────────────────────────┼──────────────────────────────────────┘
                           │
┌──────────────────────────┼──────────────────────────────────────┐
│                          ▼            SELEFACE LAYER            │
│                 ┌─────────────────┐                             │
│                 │     Client      │  ← undetected-chromedriver  │
│                 │  (uc.Chrome)    │                             │
│                 └────────┬────────┘                             │
│                          │                                      │
│    ┌─────────────────────┼─────────────────────┐                │
│    ▼                     ▼                     ▼                │
│ ┌──────┐  ┌───────┐  ┌──────┐  ┌──────┐  ┌──────┐               │
│ │React │  │Comment│  │Share │  │Follow│  │Login │  ← Methods    │
│ └──────┘  └───────┘  └──────┘  └──────┘  └──────┘               │
└─────────────────────────────────────────────────────────────────┘
                           │
┌──────────────────────────┼──────────────────────────────────────┐
│                          ▼            PROXY LAYER               │
│    ┌─────────────────────────────────────────┐                  │
│    │         ProxyManager (DataImpulse)      │                  │
│    │  • Generates sticky session IDs         │                  │
│    │  • Creates proxy URL per account        │                  │
│    └─────────────────┬───────────────────────┘                  │
│                      ▼                                          │
│    ┌─────────────────────────────────────────┐                  │
│    │    Dynamic Chrome Extension (MV3)       │                  │
│    │  • chrome.proxy.settings.set()          │                  │
│    │  • chrome.webRequest.onAuthRequired     │                  │
│    └─────────────────────────────────────────┘                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📂 Project Structure

```
FacebookBotV1.1.1/
│
├── main.py                         # Application entry point
├── requirements.txt                # Python dependencies
├── .env                            # Environment configuration (create from .env.example)
├── .env.example                    # Environment template
├── .gitignore                      # Git ignore rules
├── bot.log                         # Application logs (auto-generated)
│
├── cookies/                        # Stored Facebook cookies (per account)
│   └── {email}.json                # Cookie file per account
│
├── database/                       # Database layer
│   ├── __init__.py
│   ├── database.py                 # JSON-based data persistence
│   └── bot_data.json               # User/account data storage
│
├── generated_extensions/           # Dynamic proxy extensions (auto-generated)
│   └── proxy_{host}_{port}/        # Extension per proxy config
│       ├── manifest.json           # MV3 manifest
│       └── background.js           # Proxy + auth service worker
│
├── handlers/                       # Telegram command handlers
│   ├── __init__.py
│   ├── accounts.py                 # Account management (list/check/delete/relogin)
│   ├── admin.py                    # Admin-only commands
│   ├── help.py                     # Help command
│   ├── login.py                    # Facebook login (manual + cookies)
│   ├── services.py                 # Facebook services (react/comment/share/follow)
│   └── start.py                    # Bot start/home commands
│
├── profiles/                       # Browser profiles (auto-created)
│   └── {account_id}/               # Isolated profile per account
│       ├── Default/                # Chrome default profile
│       └── Local State             # Chrome local state
│
├── screenshots/                    # Debug screenshots (auto-cleaned on start)
│
├── seleface/                       # Core Facebook automation library
│   ├── __init__.py
│   ├── client.py                   # Anti-detect Chrome client (main class)
│   ├── logger.py                   # Custom colored logging
│   │
│   ├── methods/                    # Facebook action methods
│   │   ├── __init__.py             # Methods aggregator
│   │   ├── actions/
│   │   │   ├── __init__.py
│   │   │   ├── comment.py          # Comment on posts
│   │   │   ├── follow.py           # Follow pages/profiles
│   │   │   ├── react.py            # React to posts (like/love/etc)
│   │   │   └── share.py            # Share posts
│   │   └── login/
│   │       ├── __init__.py
│   │       ├── cookies.py          # Cookie-based login
│   │       └── login.py            # Credential-based login
│   │
│   └── utils/
│       ├── __init__.py
│       ├── helpers.py              # Utility functions
│       ├── proxy_extension.py      # Dynamic MV3 extension generator
│       └── proxy_manager.py        # DataImpulse proxy integration
│
└── utils/                          # Shared utilities
    ├── __init__.py
    ├── facebook_utils.py           # High-level Facebook operations
    └── telegram_utils.py           # Telegram UI helpers (Arabic text, keyboards)
```

---

## 🚀 Installation

### Prerequisites

| Requirement   | Version | Notes                              |
| ------------- | ------- | ---------------------------------- |
| Python        | 3.8+    | Required                           |
| Google Chrome | 108+    | Required (MV3 extension support)   |
| Linux         | Any     | Tested on Fedora, Ubuntu, Pop!\_OS |
| pip           | Latest  | Python package manager             |

### Step 1: System Dependencies

**Fedora/RHEL:**

```bash
sudo dnf install -y python3 python3-pip google-chrome-stable
```

**Ubuntu/Debian:**

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv

# Install Chrome
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb
sudo apt --fix-broken install -y
```

### Step 2: Project Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/FacebookBotV1.1.1.git
cd FacebookBotV1.1.1

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit with your credentials
nano .env
```

---

## ⚙️ Configuration

### Environment Variables (.env)

```env
# ═══════════════════════════════════════════════════════════════
# TELEGRAM BOT CONFIGURATION
# ═══════════════════════════════════════════════════════════════

# Get from https://my.telegram.org/apps
API_ID=12345678
API_HASH=your_api_hash_here

# Get from @BotFather on Telegram
BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz

# ═══════════════════════════════════════════════════════════════
# BOT ACCESS CONTROL (Superuser Credentials)
# ═══════════════════════════════════════════════════════════════

SUSERNAME=admin
PASSWORD=your_secure_password_here

# ═══════════════════════════════════════════════════════════════
# DATAIMPULSE PROXY CONFIGURATION (Optional but Recommended)
# ═══════════════════════════════════════════════════════════════

# Get from https://dataimpulse.com/dashboard
DATAIMPULSE_USERNAME=your_username
DATAIMPULSE_PASSWORD=your_password
DATAIMPULSE_HOST=gw.dataimpulse.com
DATAIMPULSE_PORT=823

# ═══════════════════════════════════════════════════════════════
# OPTIONAL SETTINGS
# ═══════════════════════════════════════════════════════════════

# Database path (default: ./database/bot_data.json)
DB_PATH=./database/bot_data.json

# Screenshots directory (default: ./screenshots)
SCREENSHOTS_DIR=./screenshots
```

### Telegram Bot Setup

1. **Create a bot with @BotFather:**

   ```
   /newbot
   → Name: Facebook Automation Bot
   → Username: your_fb_bot
   ```

2. **Get API credentials from https://my.telegram.org:**

   - Login with your phone number
   - Go to "API development tools"
   - Create a new application
   - Copy `api_id` and `api_hash`

3. **Configure bot commands with @BotFather:**
   ```
   /setcommands
   start - بدء استخدام البوت
   help - عرض المساعدة
   cancel - إلغاء الأمر الحالي
   login - تسجيل الدخول إلى حساب فيسبوك
   services - عرض الخدمات المتاحة
   accounts - إدارة الحسابات
   ```

---

## 🎮 Usage

### Starting the Bot

```bash
# Activate virtual environment
source venv/bin/activate

# Run the bot
python main.py
```

**Expected output:**

```
2026-01-05 12:00:00 - __main__ - INFO - Starting Facebook Automation Bot...
2026-01-05 12:00:01 - pyrogram.client - INFO - Pyrogram v2.x.x started
2026-01-05 12:00:01 - __main__ - INFO - Bot is running. Press Ctrl+C to stop.
```

### First-Time Setup Flow

1. **Start the bot:** Send `/start` to your bot
2. **Authenticate:** Enter the superuser credentials from `.env`
3. **Add account:** Click "Add Account" → "Password Login"
4. **Login:** Enter Facebook email → Browser opens → Login manually
5. **Confirm:** Click "Done / Save Session" after successful login
6. **Use services:** Go to `/services` and select an action

### Using Services

```
/services
  ↓
┌─────────────────────────────────┐
│  👍 React to Post               │
│  💬 Comment on Post             │
│  🔄 Share Post                  │
│  ➕ Follow Page/Profile         │
└─────────────────────────────────┘
  ↓
Enter post/page URL
  ↓
Select accounts to use
  ↓
Action executed with warm-up + auto-save
```

---

## 📱 Telegram Commands

| Command     | Description                           |
| ----------- | ------------------------------------- |
| `/start`    | Start the bot and show authentication |
| `/login`    | Login to a Facebook account           |
| `/accounts` | Manage saved Facebook accounts        |
| `/services` | Access Facebook automation services   |
| `/help`     | Display help and available commands   |
| `/cancel`   | Cancel the current operation          |

### Account Management Features

| Action      | Description                                          |
| ----------- | ---------------------------------------------------- |
| **List**    | View all connected Facebook accounts                 |
| **Check**   | Verify if account session is still valid             |
| **Relogin** | Delete profile + cookies, login fresh with new proxy |
| **Delete**  | Remove account from the system                       |

---

## 🛡️ Anti-Detection Techniques

### 1. Undetected ChromeDriver

The bot uses `undetected-chromedriver` which automatically patches Chrome to:

- Remove `navigator.webdriver` flag
- Patch `window.chrome.cdc_*` properties
- Randomize WebGL fingerprint
- Modify automation-related JavaScript properties

### 2. No MITM Proxy (Critical)

**Problem:** Selenium-Wire uses a local MITM proxy that Facebook detects, triggering reCAPTCHA.

**Solution:** We use a Chrome extension for proxy authentication:

```javascript
// Generated MV3 extension - no MITM required
chrome.webRequest.onAuthRequired.addListener(
  (details, callback) => {
    callback({
      authCredentials: { username: PROXY_USER, password: PROXY_PASS },
    });
  },
  { urls: ["<all_urls>"] },
  ["asyncBlocking"]
);
```

### 3. IP Kill Switch

Before any operation, the bot verifies the proxy is working:

```python
# Visits https://api.ip.sb/geoip to check IP
# If IP is from blocked country (e.g., Egypt), aborts immediately
if country_code == "EG":
    raise ConnectionError("Proxy Leak Detected!")
```

### 4. Human-Like Behavior

- **Warm-up visits:** Opens Facebook home before actions
- **Randomized delays:** 2-4 second pauses between actions
- **Natural typing:** (Planned) Variable keystroke timing

### 5. Profile Isolation

Each account has:

- Dedicated `user-data-dir`
- Separate cookies
- Isolated local storage
- Unique proxy session ID

---

## 🔌 Proxy Extension System

### How It Works

1. **ProxyManager** generates a proxy URL with sticky session:

   ```
   http://username__sessid.abc123:password@gw.dataimpulse.com:823
   ```

2. **create_proxy_extension()** generates a Chrome extension:

   ```
   generated_extensions/proxy_gw_dataimpulse_com_823/
   ├── manifest.json    # MV3 manifest
   └── background.js    # Service worker with auth
   ```

3. **Client** loads the extension via Chrome flags:
   ```
   --load-extension=/path/to/generated_extensions/proxy_...
   ```

### Extension Structure (MV3)

**manifest.json:**

```json
{
  "manifest_version": 3,
  "name": "Proxy Auth Helper",
  "permissions": ["proxy", "webRequest", "webRequestAuthProvider"],
  "host_permissions": ["<all_urls>"],
  "background": {
    "service_worker": "background.js",
    "type": "module"
  }
}
```

**background.js:**

```javascript
// Configure proxy
chrome.proxy.settings.set({
  value: {
    mode: "fixed_servers",
    rules: {
      singleProxy: { scheme: "http", host: HOST, port: PORT },
    },
  },
});

// Handle authentication
chrome.webRequest.onAuthRequired.addListener(
  (details, callback) => {
    callback({ authCredentials: { username, password } });
  },
  { urls: ["<all_urls>"] },
  ["asyncBlocking"]
);
```

---

## 📊 Account Management

### Adding an Account

**Method 1: Manual Login (Recommended)**

1. Go to `/login` → "Password Login"
2. Enter Facebook email
3. Browser opens (visible mode)
4. Login manually (handle 2FA if needed)
5. Click "Done / Save Session"

**Method 2: Cookie Import (Disabled by default)**

- Can be enabled in `handlers/login.py`
- Accepts JSON cookie files

### Relogin Feature

When an account needs fresh credentials:

1. Go to `/accounts` → Select account
2. Click "🔄 Relogin"
3. Confirm the warning (deletes profile + cookies)
4. Login fresh with new proxy

**What gets deleted:**

- Browser profile (`profiles/{account_id}/`)
- Cookies file (`cookies/{email}.json`)
- Account record (re-added after successful login)

### Cookie Auto-Save

After every successful action:

```python
# In FacebookUtils
if result.get("status") == "ok":
    self._auto_save_cookies_if_enabled()
```

This keeps sessions fresh and prevents token expiration.

---

## 🔧 API Reference

### Client Class

```python
from seleface import Client

# Initialize with options
client = Client(
    headless=True,              # Run in headless mode
    wait_until_duration=30,     # WebDriverWait timeout
    enable_mobile_emulation=False,
    account_id="user@email.com", # Profile isolation
    proxy="http://user:pass@host:port",
    optimize_bandwidth=True,    # Block CSS/fonts
    load_images=False           # Block images
)

# Login with cookies
client.login(email, use_cookies=True, cookies_file="path/to/cookies.json")

# Perform actions
client.react(post_url, react="Like")
client.comment(post_url, cmnt="Great post!")
client.share(post_url)
client.follow(page_url)

# Cleanup
client.quit()
```

### FacebookUtils Class

```python
from utils.facebook_utils import FacebookUtils

# Initialize
fb = FacebookUtils(
    proxy="http://...",
    account_id="user@email.com",
    optimize_bandwidth=True,
    load_images=False,
    auto_save_cookies=True  # Auto-save after success
)

# Login
result, screenshot = fb.login(
    email="user@email.com",
    cookies_file="cookies/user@email.com.json",
    use_cookies=True
)

# Actions (with warm-up + auto-save)
result, screenshot = fb.react_post(post_url, react_type="Like")
result, screenshot = fb.comment_post(post_url, comment_text="Nice!")
result, screenshot = fb.share_post(post_url)
result, screenshot = fb.follow_page(page_url)

# Cleanup
fb.close()
```

### ProxyManager

```python
from seleface.utils.proxy_manager import ProxyManager

# Initialize from environment
pm = ProxyManager.from_env()

# Generate proxy URL for account
proxy_url = pm.get_new_proxy(account_id="user@email.com")
# Returns: http://username__sessid.abc123:password@host:port
```

---

## 🔧 Troubleshooting

### Common Issues

| Issue                 | Cause                    | Solution                                        |
| --------------------- | ------------------------ | ----------------------------------------------- |
| Chrome not found      | Chrome not installed     | `sudo apt install google-chrome-stable`         |
| Extension not loading | Chrome flags disabled    | Update Chrome to 108+                           |
| Proxy leak (Egypt IP) | Extension failed         | Check proxy credentials, restart                |
| reCAPTCHA on login    | Detection triggered      | Use manual login, avoid automation during login |
| Session expired       | Cookies stale            | Use relogin feature                             |
| "Invalid session ID"  | Browser crashed          | Restart the bot                                 |
| Profile locked        | Previous session running | Kill Chrome processes: `pkill chrome`           |

### Debug Mode

Enable visible browser for debugging:

```python
# In handlers/login.py - already enabled for manual login
facebook._init_client_safe(
    headless=False,  # Visible browser
    load_images=True # Show images
)
```

### Logs

Check `bot.log` for detailed logs:

```bash
tail -f bot.log
```

### Clean Restart

```bash
# Kill any running Chrome processes
pkill -f chrome

# Clear generated extensions
rm -rf generated_extensions/

# Clear screenshots
rm -rf screenshots/*

# Restart
python main.py
```

---

## 🔒 Security Considerations

### Credentials Safety

- ⚠️ Never commit `.env` to version control
- ⚠️ Use strong passwords for bot authentication
- ⚠️ DataImpulse credentials are embedded in extensions (local only)

### Facebook Account Safety

- ✅ Use accounts you own or have permission to automate
- ✅ Use residential proxies (DataImpulse) to avoid detection
- ✅ Don't run excessive automation (rate limit yourself)
- ✅ Use the relogin feature if account gets flagged

### IP Protection

The IP Kill Switch prevents operations if:

- Proxy fails to connect
- Real IP is detected (blocked country)
- Proxy returns wrong geo-location

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## 📄 License

This project is for educational purposes only. Use responsibly and in accordance with Facebook's Terms of Service.

---

<div align="center">

**Built with ❤️ using Python, Pyrogram, and undetected-chromedriver**

**v1.1.1** | January 2026

</div>
