import json
import os
import shutil
import time
from typing import Optional
from urllib.parse import unquote, urlparse

# استيراد Undetected Chrome فقط (بدون Selenium-Wire)
# Selenium-Wire بيتسبب في reCAPTCHA لأن فيسبوك بيكتشفه
import undetected_chromedriver as uc

from selenium.webdriver.support.wait import WebDriverWait

from seleface.logger import Logger
from seleface.methods import Methods
from seleface.utils.proxy_extension import create_proxy_extension


class Client(uc.Chrome, Methods):
    """
    Final Facebook Client using Undetected-Chromedriver with Proxy Extension.

    Why this is the chosen solution:
    1. Uses dynamic proxy extension for auth (No Selenium-Wire detection).
    2. Uses 'undetected' patcher to hide bot signature.
    3. Avoids reCAPTCHA triggers caused by Selenium-Wire's MITM proxy.
    """

    logger = Logger.get_logger("seleface.client")

    # IP Kill Switch Configuration
    BLOCKED_COUNTRY_CODE = "EG"
    BLOCKED_COUNTRY_NAME = "Egypt"
    IP_CHECK_URL = "https://api.ip.sb/geoip"
    IP_CHECK_RETRIES = 3
    IP_CHECK_TIMEOUT = 30

    # Mobile User Agent
    MOBILE_USER_AGENT = (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) "
        "Version/16.6 Mobile/15E148 Safari/604.1"
    )

    def __init__(
        self,
        headless: bool = False,
        wait_until_duration: int = 30,
        enable_mobile_emulation: bool = False,
        termux: bool = False,
        account_id: Optional[str] = None,
        proxy: Optional[str] = None,
        optimize_bandwidth: bool = True,
        load_images: bool = False,
    ):
        self.logger.info(
            f"Initializing Client (Headless={headless}, Mobile={enable_mobile_emulation}, ID={account_id})"
        )

        self._account_id = account_id
        self._proxy_extension_path = None  # Track generated extension for cleanup
        self.enable_mobile_emulation = enable_mobile_emulation
        
        # إعداد خيارات Chrome (Undetected)
        options = uc.ChromeOptions()

        # قائمة الإضافات المطلوب تحميلها
        extensions_to_load = []

        # إضافة FB_Verify_Delayer
        # fb_verifier_path = os.path.abspath("FB_Verify_Delayer")
        # if os.path.exists(fb_verifier_path):
        #     extensions_to_load.append(fb_verifier_path)
        #     self.logger.info(f"Loading FB_Verify_Delayer from: {fb_verifier_path}")

        # إعداد البروكسي عن طريق Extension (بدلاً من Selenium-Wire)
        if proxy:
            proxy_conf = self._parse_proxy(proxy)
            scheme = proxy_conf["scheme"]
            user = proxy_conf["username"]
            password = proxy_conf["password"]
            host = proxy_conf["host"]
            port = proxy_conf["port"]

            # إنشاء extension البروكسي ديناميكياً
            self._proxy_extension_path = create_proxy_extension(
                host=host,
                port=port,
                username=user if user else None,
                password=password if password else None,
                scheme=scheme,
            )
            extensions_to_load.append(self._proxy_extension_path)
            self.logger.info(f"✅ Proxy Extension Created: {host}:{port}")

        # CRITICAL: Chrome 137+ disabled --load-extension by default. Re-enable it.
        options.add_argument(
            "--disable-features=DisableDisableExtensionsExceptCommandLineSwitch,DisableLoadExtensionCommandLineSwitch"
        )

        # تحميل كل الإضافات
        if extensions_to_load:
            extensions_str = ",".join(extensions_to_load)
            options.add_argument(f"--load-extension={extensions_str}")
            options.add_argument(f"--disable-extensions-except={extensions_str}")
            self.logger.info(f"Loading {len(extensions_to_load)} extension(s)")

        # ملحوظة: لو عايز الـ debugger يشتغل، لازم تفتح الـ DevTools أوتوماتيك
        # options.add_argument("--auto-open-devtools-for-tabs")

        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")

        # منع ظهور رسائل الباسورد
        prefs = {
            "profile.exit_type": "Normal",
            "profile.exited_cleanly": True,
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "signin.allowed": False,
            "profile.default_content_setting_values.cookies": 1,  # السماح بالكوكيز
            "profile.block_third_party_cookies": False,
            # DevTools: Don't ignore extension content scripts (allow debugger to work)
            "devtools": {
                "preferences": {
                    "sdb_ignore_list": "{}",  # تصفير قائمة التجاهل القديمة
                    "skipContentScripts": "false",  # إجبار عدم تخطي سكربتات الإضافة
                }
            },
        }

        # Bandwidth optimization: Block CSS/fonts if enabled
        if optimize_bandwidth:
            prefs.update(
                {
                    "profile.managed_default_content_settings.stylesheets": 2,
                    "profile.managed_default_content_settings.fonts": 2,
                }
            )

        # Image loading: Block images by default unless load_images=True
        # This is separate from optimize_bandwidth for manual login visibility
        if not load_images:
            # PERFORMANCE: Use 'eager' strategy to stop waiting for images/stylesheets
            # This drastically reduces wait times on slow proxies
            options.page_load_strategy = "eager"
            prefs.update(
                {
                    "profile.managed_default_content_settings.images": 2,
                }
            )
        else:
            prefs.update(
                {
                    "profile.managed_default_content_settings.images": 1,
                }
            )

        options.add_experimental_option("prefs", prefs)

        if enable_mobile_emulation:
            options.add_argument(f"--user-agent={self.MOBILE_USER_AGENT}")
            options.add_argument(f"--window-size=390,844")
            options.add_argument("--enable-touch-events")

        if headless:
            options.add_argument("--headless=new")

        # عزل البروفايل
        if account_id:
            profile_dir = self._get_profile_dir(account_id)
            options.add_argument(f"--user-data-dir={profile_dir}")

        # 4. تشغيل المتصفح (Undetected Chrome)
        try:
            # use_subprocess=True مهم جداً لـ Linux
            super().__init__(
                options=options,
                use_subprocess=True,
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize Chrome driver: {e}")
            raise e

        self.wait = WebDriverWait(self, wait_until_duration)

        # 5. IP Kill Switch (الأمان الأخير)
        if proxy:
            self._validate_proxy_ip()

    def _parse_proxy(self, proxy_string: str) -> dict:
        if not proxy_string.startswith(("http", "socks")):
            proxy_string = f"http://{proxy_string}"
        parsed = urlparse(proxy_string)
        return {
            "scheme": parsed.scheme or "http",
            "host": parsed.hostname,
            "port": parsed.port,
            "username": unquote(parsed.username) if parsed.username else "",
            "password": unquote(parsed.password) if parsed.password else "",
        }

    def _validate_proxy_ip(self) -> None:
        """IP Kill Switch"""
        self.logger.info("🛡️ Validating Proxy Connection...")

        for attempt in range(1, self.IP_CHECK_RETRIES + 1):
            try:
                self.set_page_load_timeout(self.IP_CHECK_TIMEOUT)
                self.get(self.IP_CHECK_URL)

                # قراءة الرد (JSON)
                page_text = self.find_element("tag name", "body").text
                try:
                    ip_data = json.loads(page_text)
                except:
                    # أحياناً الموقع بيرجع HTML لو فيه إيرور، نجرب مرة كمان
                    time.sleep(1)
                    continue

                country = ip_data.get("country_code", "UNKNOWN")
                ip = ip_data.get("ip", "Unknown")

                if country.upper() == self.BLOCKED_COUNTRY_CODE:
                    self.logger.critical(f"🚨 PROXY LEAK! IP is {country}. Aborting.")
                    try:
                        self.quit()
                    except:
                        pass
                    raise ConnectionError(f"Proxy Leak Detected: {ip} ({country})")

                self.logger.info(f"✅ Proxy Secured: {ip} ({country})")
                self.set_page_load_timeout(30)
                return

            except Exception as e:
                self.logger.warning(f"Check {attempt} failed: {e}")
                time.sleep(2)

        try:
            self.quit()
        except:
            pass
        raise ConnectionError("Failed to validate proxy connection.")

    def _get_profile_dir(self, account_id: str) -> str:
        safe_id = account_id.replace("@", "_").replace(".", "_")
        path = os.path.join(os.getcwd(), "profiles", safe_id)
        os.makedirs(path, exist_ok=True)
        # Configure DevTools preferences in profile
        self._configure_devtools_preferences(path)
        return path

    def _configure_devtools_preferences(self, profile_dir: str) -> None:
        """Configure DevTools to NOT ignore content scripts from extensions.

        This ensures the debugger can pause on extension content scripts.
        """
        default_dir = os.path.join(profile_dir, "Default")
        os.makedirs(default_dir, exist_ok=True)
        prefs_path = os.path.join(default_dir, "Preferences")

        # Load existing preferences or start fresh
        prefs = {}
        if os.path.exists(prefs_path):
            try:
                with open(prefs_path, "r", encoding="utf-8") as f:
                    prefs = json.load(f)
            except Exception:
                prefs = {}

        # Set DevTools to NOT skip content scripts in ignore list
        if "devtools" not in prefs:
            prefs["devtools"] = {}
        if "preferences" not in prefs["devtools"]:
            prefs["devtools"]["preferences"] = {}

        # Key setting: skipContentScripts = "false" (string, not boolean)
        prefs["devtools"]["preferences"]["skipContentScripts"] = "false"

        with open(prefs_path, "w", encoding="utf-8") as f:
            json.dump(prefs, f, indent=2)

    def quit(self):
        try:
            super().quit()
        except:
            pass
        # تنظيف ملفات الإضافات المؤقتة (اختياري - تركها للتصحيح)
        # if self._proxy_extension_path and os.path.exists(self._proxy_extension_path):
        #     shutil.rmtree(self._proxy_extension_path, ignore_errors=True)
