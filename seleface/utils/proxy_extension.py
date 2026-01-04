"""
Dynamic Proxy Extension Generator for Chrome MV3

This module generates a Chrome extension dynamically with embedded proxy credentials.
For MV3, we use a service worker and chrome.proxy API.

Important: MV3 does NOT support webRequestBlocking for auth interception.
The workaround is to use:
1. chrome.proxy.settings for proxy configuration
2. chrome.webRequest.onAuthRequired with a callback (async, not blocking)
   - MV3 allows async auth handling via returning a Promise
"""

import json
import os
import shutil
import tempfile
from typing import Optional


def create_proxy_extension(
    host: str,
    port: int,
    username: Optional[str] = None,
    password: Optional[str] = None,
    scheme: str = "http",
    extension_dir: Optional[str] = None,
) -> str:
    """
    Create a Chrome extension for proxy authentication using Manifest V3.

    Args:
        host: Proxy server hostname
        port: Proxy server port
        username: Proxy username (optional)
        password: Proxy password (optional)
        scheme: Proxy scheme (http, https, socks4, socks5)
        extension_dir: Directory to create extension in (default: temp dir)

    Returns:
        Path to the extension directory
    """
    # Create extension directory
    if extension_dir is None:
        extension_dir = os.path.join(
            os.getcwd(),
            "generated_extensions",
            f"proxy_{host.replace('.', '_')}_{port}",
        )

    # Clean up old extension if exists
    if os.path.exists(extension_dir):
        shutil.rmtree(extension_dir)

    os.makedirs(extension_dir, exist_ok=True)

    # Generate manifest.json (MV3)
    manifest = {
        "manifest_version": 3,
        "name": "Proxy Auth Helper",
        "version": "1.0.0",
        "description": "Handles proxy authentication",
        "permissions": ["proxy", "storage", "webRequest", "webRequestAuthProvider"],
        "host_permissions": ["<all_urls>"],
        "background": {"service_worker": "background.js", "type": "module"},
        "minimum_chrome_version": "108.0.0",
    }

    manifest_path = os.path.join(extension_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # Generate background.js with embedded credentials
    # Escape special characters in credentials
    safe_username = json.dumps(username or "")
    safe_password = json.dumps(password or "")

    # Determine proxy scheme for config
    proxy_scheme = scheme.lower()
    if proxy_scheme.startswith("socks"):
        proxy_scheme = "socks5" if "5" in scheme else "socks4"
    else:
        proxy_scheme = "http"

    background_js = f"""// Auto-generated Proxy Extension (MV3)
// Host: {host}:{port}
// Generated dynamically for secure proxy authentication

const PROXY_HOST = "{host}";
const PROXY_PORT = {port};
const PROXY_USER = {safe_username};
const PROXY_PASS = {safe_password};
const PROXY_SCHEME = "{proxy_scheme}";

// 1. Register auth handler for proxy authentication (MV3 async style)
if (PROXY_USER && PROXY_PASS) {{
    chrome.webRequest.onAuthRequired.addListener(
        (details, callback) => {{
            console.log("🔐 Proxy auth requested for:", details.challenger.host);
            callback({{
                authCredentials: {{
                    username: PROXY_USER,
                    password: PROXY_PASS
                }}
            }});
        }},
        {{ urls: ["<all_urls>"] }},
        ["asyncBlocking"]
    );
    console.log("✅ Proxy auth handler registered (MV3 async)");
}}

// 2. Configure the proxy
const proxyConfig = {{
    mode: "fixed_servers",
    rules: {{
        singleProxy: {{
            scheme: PROXY_SCHEME,
            host: PROXY_HOST,
            port: PROXY_PORT
        }},
        bypassList: ["localhost", "127.0.0.1", "*.local"]
    }}
}};

chrome.proxy.settings.set(
    {{ value: proxyConfig, scope: "regular" }},
    () => {{
        if (chrome.runtime.lastError) {{
            console.error("❌ Proxy config failed:", chrome.runtime.lastError.message);
        }} else {{
            console.log("✅ Proxy configured:", PROXY_HOST + ":" + PROXY_PORT);
        }}
    }}
);

console.log("✅ Proxy Extension Loaded (MV3)");
"""

    background_path = os.path.join(extension_dir, "background.js")
    with open(background_path, "w", encoding="utf-8") as f:
        f.write(background_js)

    return extension_dir


def cleanup_proxy_extensions(base_dir: Optional[str] = None) -> None:
    """Clean up all generated proxy extensions."""
    if base_dir is None:
        base_dir = os.path.join(os.getcwd(), "generated_extensions")

    if os.path.exists(base_dir):
        shutil.rmtree(base_dir, ignore_errors=True)
