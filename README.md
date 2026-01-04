# 🤖 Facebook Automation Bot

<div align="center">

**A powerful Telegram-controlled Facebook Automation Bot with advanced anti-detect capabilities**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Telegram](https://img.shields.io/badge/Telegram-Bot%20API-blue.svg)](https://core.telegram.org/bots)
[![Selenium](https://img.shields.io/badge/Selenium-WebDriver-green.svg)](https://selenium.dev)
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
- [Troubleshooting](#-troubleshooting)

---

## 🎯 Overview

This bot provides a seamless interface to automate Facebook operations through Telegram. Built with a focus on **stealth and reliability**, it employs advanced anti-detection mechanisms to ensure stable, long-term automation.

### Tech Stack

| Technology                  | Purpose                        |
| --------------------------- | ------------------------------ |
| **Python 3.8+**             | Core language                  |
| **Pyrogram / Pyrofork**     | Telegram Bot framework         |
| **undetected-chromedriver** | Anti-detect browser automation |
| **Selenium WebDriver**      | Browser control                |
| **DataImpulse**             | Residential proxy network      |

---

## ✨ Key Features

### 🛡️ Anti-Detect System

The bot uses a sophisticated anti-detection architecture to bypass Facebook's bot detection mechanisms:

- **Undetected ChromeDriver**: Leverages [`undetected-chromedriver`](https://github.com/ultrafunkamsterdam/undetected-chromedriver) to patch Chrome and evade automated browser detection.
- **Mobile Emulation**: Emulates real mobile devices (iPhone/Pixel) with authentic viewport sizes and user agents:
  ```python
  mobile_emulation = {
      "deviceMetrics": {"width": 390, "height": 844, "pixelRatio": 3.0},
      "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) ..."
  }
  ```
- **Randomized Behavior**: Implements human-like delays and interactions to avoid pattern detection.

### 🌐 Smart Proxy Management (DataImpulse Integration)

The bot integrates with **DataImpulse Residential Proxies** for IP masking and geo-targeting:

- **Sticky Sessions**: Each Facebook account receives a unique session ID (`__sessid.{random_id}`) ensuring the same IP is maintained across all requests for that account:
  ```
  Format: http://{username}__sessid.{session_id}:{password}@gw.dataimpulse.com:823
  ```
- **IP Stability**: Critical for Facebook—consistent IPs per account prevent security triggers.
- **Geo-Targeting**: Optional country targeting via proxy configuration (e.g., `__cr.eg` for Egypt).

### 📁 Profile Isolation

Each Facebook account operates in complete isolation:

- **Dedicated User Data Directory**: Every account gets its own `--user-data-dir` in the `profiles/` folder.
- **Persistent Sessions**: Cookies, cache, and local storage are preserved per account.
- **No Cross-Contamination**: Account A's session data never interferes with Account B.

```
profiles/
├── user1_example_com/
│   ├── Default/
│   ├── Cookies
│   └── Local Storage/
└── user2_example_com/
    ├── Default/
    ├── Cookies
    └── Local Storage/
```

### 📊 Bandwidth Optimization

To minimize proxy data costs, the bot blocks unnecessary resources:

| Resource Type   | Status     |
| --------------- | ---------- |
| Images          | ❌ Blocked |
| CSS Stylesheets | ❌ Blocked |
| Fonts           | ❌ Blocked |
| Plugins         | ❌ Blocked |
| Popups          | ❌ Blocked |
| Notifications   | ❌ Blocked |
| Media Streams   | ❌ Blocked |

This significantly reduces bandwidth consumption while maintaining full functionality for automation tasks.

---

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Telegram      │────▶│    Pyrogram     │────▶│    Handlers     │
│   User/Client   │◀────│    Bot Core     │◀────│   (Commands)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                         │
                                                         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   DataImpulse   │◀────│  ProxyManager   │◀────│   Seleface      │
│   Proxy Network │     │                 │     │   (Client)      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │    Facebook     │
                                                │   (Automation)  │
                                                └─────────────────┘
```

---

## 📂 Project Structure

```
FacebookBotV1.1.1/
│
├── main.py                     # Application entry point
├── requirements.txt            # Python dependencies
├── .env                        # Environment configuration (create this)
├── bot.log                     # Application logs
│
├── cookies/                    # Stored Facebook cookies
├── database/                   # Database layer
│   ├── __init__.py
│   └── database.py             # JSON-based data persistence
│
├── handlers/                   # Telegram command handlers
│   ├── accounts.py             # Account management commands
│   ├── admin.py                # Admin-only commands
│   ├── help.py                 # Help command
│   ├── login.py                # Facebook login handlers
│   ├── services.py             # Facebook services (react, comment, etc.)
│   └── start.py                # Bot start/home commands
│
├── profiles/                   # Browser profiles (auto-created)
├── screenshots/                # Debug screenshots
│
├── seleface/                   # Facebook automation library
│   ├── __init__.py
│   ├── client.py               # Anti-detect Chrome client
│   ├── logger.py               # Custom logging
│   ├── methods/                # Facebook action methods
│   │   ├── __init__.py
│   │   ├── actions/
│   │   │   ├── comment.py      # Comment automation
│   │   │   ├── follow.py       # Follow automation
│   │   │   ├── react.py        # Reaction automation
│   │   │   └── share.py        # Share automation
│   │   └── login/
│   │       ├── cookies.py      # Cookie-based login
│   │       └── login.py        # Credential-based login
│   └── utils/
│       ├── __init__.py
│       ├── helpers.py          # Utility functions
│       └── proxy_manager.py    # DataImpulse proxy integration
│
└── utils/                      # Shared utilities
    ├── __init__.py
    ├── facebook_utils.py       # Facebook helper functions
    └── telegram_utils.py       # Telegram UI helpers
```

---

## 🚀 Installation

### Prerequisites

| Requirement             | Version | Notes             |
| ----------------------- | ------- | ----------------- |
| Python                  | 3.8+    | Required          |
| Google Chrome           | Latest  | Must be installed |
| Linux (Pop!\_OS/Ubuntu) | Any     | Recommended OS    |

### System Dependencies (Linux/Pop!\_OS)

```bash
# Update package list
sudo apt update

# Install Chrome (if not installed)
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb
sudo apt --fix-broken install

# Install required system packages
sudo apt install -y python3-pip python3-venv
```

### Project Setup

```bash
# Clone the repository
git clone <repository-url>
cd FacebookBotV1.1.1

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Dependencies

```
pyrogram          # Telegram MTProto framework
pyrofork          # Pyrogram fork with additional features
pillow            # Image processing
python-dotenv     # Environment variable management
selenium          # Browser automation
webdriver-manager # ChromeDriver management
undetected-chromedriver  # Anti-detect browser
colorlog          # Colored console logging
```

---

## ⚙️ Configuration

Create a `.env` file in the project root with the following variables:

```env
# ═══════════════════════════════════════════════════════════════
# TELEGRAM BOT CONFIGURATION
# ═══════════════════════════════════════════════════════════════

# Get these from https://my.telegram.org/apps
API_ID=your_api_id
API_HASH=your_api_hash

# Get this from @BotFather on Telegram
BOT_TOKEN=your_bot_token

# ═══════════════════════════════════════════════════════════════
# SUPERUSER CREDENTIALS (Bot Access Control)
# ═══════════════════════════════════════════════════════════════

# Username and password for bot authentication
SUSERNAME=admin
PASSWORD=your_secure_password

# ═══════════════════════════════════════════════════════════════
# DATAIMPULSE PROXY CONFIGURATION (Required for Proxy Support)
# ═══════════════════════════════════════════════════════════════

# Your DataImpulse account credentials
# Get these from https://dataimpulse.com/dashboard
DATAIMPULSE_USERNAME=your_dataimpulse_username
DATAIMPULSE_PASSWORD=your_dataimpulse_password

# Optional: Proxy host and port (defaults shown)
# DATAIMPULSE_HOST=gw.dataimpulse.com
# DATAIMPULSE_PORT=823

# ═══════════════════════════════════════════════════════════════
# OPTIONAL SETTINGS
# ═══════════════════════════════════════════════════════════════

# Database file path (default: ./database/bot_data.json)
# DB_PATH=./database/bot_data.json

# Screenshots directory (default: ./screenshots)
# SCREENSHOTS_DIR=./screenshots
```

### DataImpulse Proxy Format

The proxy manager automatically formats credentials for sticky sessions:

```
Input:
  Username: myuser
  Password: mypass

Output (per account):
  http://myuser__sessid.ab12cd34:mypass@gw.dataimpulse.com:823
          └────┬─────┘└────┬────┘
          base user    session ID
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

The bot will:

1. Load environment variables from `.env`
2. Initialize the database
3. Connect to Telegram
4. Register command handlers
5. Start listening for messages

### Logs

Logs are written to both console (colored) and `bot.log` file:

```
2026-01-01 12:00:00 - seleface.client - INFO - Initializing Facebook Client...
2026-01-01 12:00:01 - seleface.proxy_manager - INFO - Generated proxy for account 'user@example.com'
```

---

## 📱 Telegram Commands

| Command     | Description                                          |
| ----------- | ---------------------------------------------------- |
| `/start`    | Start the bot and show authentication options        |
| `/login`    | Login to a Facebook account (credentials or cookies) |
| `/accounts` | Manage saved Facebook accounts                       |
| `/services` | Access Facebook automation services                  |
| `/help`     | Display help and available commands                  |
| `/cancel`   | Cancel the current operation                         |

### Login Methods

1. **Credentials Login** (Not recommended)

   - Enter email/phone and password
   - May trigger 2FA or security checks

2. **Cookie Login** (Recommended)
   - Upload a JSON cookie file
   - Or paste cookies in `email:cookie_string` format
   - Most reliable method

### Available Services

After logging in, you can access various Facebook automation services:

- 👍 **React** to posts
- 💬 **Comment** on posts
- 🔄 **Share** posts
- ➕ **Follow** profiles/pages

---

## 🔧 Troubleshooting

### Common Issues

| Issue                          | Solution                                                       |
| ------------------------------ | -------------------------------------------------------------- |
| Chrome not found               | Install Google Chrome: `sudo apt install google-chrome-stable` |
| ChromeDriver version mismatch  | `undetected-chromedriver` handles this automatically           |
| Proxy connection failed        | Verify DataImpulse credentials in `.env`                       |
| Facebook blocking requests     | Enable mobile emulation, use fresh proxies                     |
| Permission denied on profiles/ | Run: `chmod -R 755 profiles/`                                  |

### Debug Mode

To see browser actions (non-headless):

```python
# In your handler code
client = Client(headless=False, account_id="test")
```

---

## 📄 License

This project is for educational purposes only. Use responsibly and in accordance with Facebook's Terms of Service.

---

<div align="center">

**Built with ❤️ using Python, Pyrogram, and undetected-chromedriver**

</div>
