import os
import uuid
from io import BytesIO
from typing import Literal

from pyrogram import Client, filters
from pyrogram.enums import ListenerTypes
from pyrogram.errors import ListenerStopped, ListenerTimeout
from pyrogram.types import CallbackQuery, Message

from database.database import Database
from seleface.utils.proxy_manager import ProxyManager
from utils.facebook_utils import FacebookUtils
from utils.telegram_utils import ArabicText, create_keyboard

# Store temporary user data (including active browser sessions for manual login)
user_data = {}

# Store active browser sessions for manual login
# Format: {account_id: {"facebook": FacebookUtils, "telegram_id": int, "username": str, "proxy": str|None}}
active_manual_sessions = {}

# Initialize ProxyManager for automatic proxy assignment
proxy_manager = ProxyManager.from_env()


@Client.on_message(filters.command("login"))
async def login_command(client: Client, message: Message):
    """Handle /login command"""
    # Get user info
    telegram_id = message.from_user.id

    # Check if user is already authenticated
    db: Database = client.db
    if not db.is_authenticated(telegram_id):
        # User is not authenticated, redirect to start
        from .start import start_command

        await start_command(client, message)
        return

    # User is authenticated, show login options
    keyboard = create_keyboard(
        [
            [
                (ArabicText.LOGIN_WITH_CREDENTIALS, "login:credentials"),
                (ArabicText.LOGIN_WITH_COOKIES, "login:cookies"),
            ],
            [(ArabicText.HOME_TITLE, "home")],
        ]
    )

    await message.reply(ArabicText.LOGIN_TITLE, reply_markup=keyboard, quote=True)


@Client.on_callback_query(filters.regex(r"^(login:)"))
async def login_callback(client: Client, callback_query: CallbackQuery):
    """Handle login callbacks"""
    # Parse callback data
    data = callback_query.data.split(":", maxsplit=2)

    if len(data) < 2 or data[0] != "login":
        return

    action = data[1]
    telegram_id = callback_query.from_user.id

    # Check if user is authenticated
    db: Database = client.db
    if not db.is_authenticated(telegram_id):
        # User is not authenticated, redirect to start
        await callback_query.answer("يجب تسجيل الدخول أولاً", show_alert=True)
        return

    # Get username
    username = db.get_authenticated_username(telegram_id)

    if action == "types":
        keyboard = create_keyboard(
            [
                [
                    (ArabicText.LOGIN_WITH_CREDENTIALS, "login:credentials"),
                    (ArabicText.LOGIN_WITH_COOKIES, "login:cookies"),
                ],
                [(ArabicText.BACK, "accounts:menu")],
                [(ArabicText.HOME_TITLE, "home")],
            ]
        )

        await callback_query.edit_message_text(
            ArabicText.LOGIN_TITLE, reply_markup=keyboard
        )
    elif action == "credentials":
        # Login with credentials (Human-Assisted Manual Login)
        await login_with_credentials(client, callback_query, username)
    elif action == "cookies":
        # Login with cookies - DISABLED for security reasons
        keyboard = create_keyboard(
            [
                [(ArabicText.BACK, "login:types")],
                [(ArabicText.HOME_TITLE, "home")],
            ]
        )
        await callback_query.edit_message_text(
            "تم تعطيل هذه الطريقة لأسباب أمنية تتعلق بحماية الحسابات",
            reply_markup=keyboard,
        )
    elif action == "manual_done":
        # Handle manual login completion
        if len(data) >= 3:
            account_id = data[2]
            await handle_manual_login_done(client, callback_query, account_id, username)
        else:
            await callback_query.answer("خطأ: معرف الحساب غير موجود", show_alert=True)

    elif action == "manual_cancel":
        # Handle manual login cancellation
        if len(data) >= 3:
            account_id = data[2]
            await handle_manual_login_cancel(client, callback_query)
        else:
            await callback_query.answer("خطأ: معرف الحساب غير موجود", show_alert=True)
    elif action == "cookies:file":
        # Login with cookies file - DISABLED
        keyboard = create_keyboard(
            [
                [(ArabicText.BACK, "login:types")],
                [(ArabicText.HOME_TITLE, "home")],
            ]
        )
        await callback_query.edit_message_text(
            "تم تعطيل هذه الطريقة لأسباب أمنية تتعلق بحماية الحسابات",
            reply_markup=keyboard,
        )
    elif action == "cookies:str":
        # Login with cookies string - DISABLED
        keyboard = create_keyboard(
            [
                [(ArabicText.BACK, "login:types")],
                [(ArabicText.HOME_TITLE, "home")],
            ]
        )
        await callback_query.edit_message_text(
            "تم تعطيل هذه الطريقة لأسباب أمنية تتعلق بحماية الحسابات",
            reply_markup=keyboard,
        )


async def login_with_credentials(
    client: Client, callback_query: CallbackQuery, username: str
):
    """Handle login with credentials - Human-Assisted Manual Login"""
    telegram_id = callback_query.from_user.id

    db: Database = client.db
    if not db.is_authenticated(telegram_id):
        # User is not authenticated, redirect to start
        await callback_query.answer("يجب تسجيل الدخول أولاً", show_alert=True)
        return

    # Get username
    username = db.get_authenticated_username(telegram_id)

    keyboard = create_keyboard(
        [
            [
                (ArabicText.BACK, "login:types"),
                (ArabicText.HOME_TITLE, "home"),
            ]
        ]
    )

    # Ask for email/account identifier first
    await callback_query.edit_message_text(
        ArabicText.ENTER_EMAIL,
        reply_markup=keyboard,
    )
    try:
        email_response: Message = await client.listen(
            filters.text, user_id=telegram_id, chat_id=telegram_id, timeout=60
        )
    except (ListenerTimeout, ListenerStopped):
        await callback_query.edit_message_text(
            ArabicText.INPUT_TIMEOUT,
            reply_markup=keyboard,
        )
        return

    if email_response.text == "/cancel":
        await email_response.reply(
            "تم الغاء العملية..", quote=True, reply_markup=keyboard
        )
        return

    email = email_response.text.strip()

    # Generate a unique account ID for this session
    account_id = email.replace("@", "_").replace(".", "_")

    loading_message = await email_response.reply(
        "⏳ جاري فتح المتصفح... الرجاء الانتظار",
        quote=True,
    )

    # Automatically generate a proxy for this new account
    account_proxy = None
    if proxy_manager.is_configured():
        try:
            account_proxy = proxy_manager.get_new_proxy(account_id=email)
        except Exception as e:
            # Log the error but continue without proxy
            print(f"Warning: Failed to generate proxy for {email}: {e}")

    # Initialize FacebookUtils with proxy and account_id for anti-detect
    # Use headless=False for visible browser
    # Use load_images=True for manual login visibility
    facebook = FacebookUtils(
        proxy=account_proxy,
        account_id=email,
        optimize_bandwidth=False,  # Disable bandwidth optimization for manual login
        load_images=True,  # Enable images for human-assisted login
    )

    try:
        # Initialize browser in NON-HEADLESS (visible) mode
        facebook._init_client_safe(
            headless=False,  # VISIBLE browser
            enable_mobile_emulation=False,
            proxy=account_proxy,
            account_id=email,
            optimize_bandwidth=False,
            load_images=True,  # Enable images for human-assisted login
        )

        # Navigate to Facebook
        facebook.client.get("https://facebook.com")

        # Store the session for later use
        active_manual_sessions[account_id] = {
            "facebook": facebook,
            "telegram_id": telegram_id,
            "username": username,
            "proxy": account_proxy,
            "email": email,
        }

        # Update the loading message with instructions and Done button
        await loading_message.edit_text(
            "🌐 **تم فتح المتصفح بنجاح!**\n\n"
            "📝 **تعليمات:**\n"
            "1. قم بتسجيل الدخول إلى حسابك في نافذة المتصفح المفتوحة\n"
            "2. تأكد من إتمام عملية تسجيل الدخول بالكامل\n"
            "3. **⚠️ لا تغلق المتصفح!**\n"
            "4. بعد إتمام تسجيل الدخول، اضغط على الزر أدناه\n\n"
            f"📧 الحساب: `{email}`",
            reply_markup=create_keyboard(
                [
                    [("✅ تم / حفظ الجلسة", f"login:manual_done:{account_id}")],
                    [(ArabicText.CANCEL, f"login:manual_cancel:{account_id}")],
                ]
            ),
        )

    except Exception as e:
        # Clean up on error
        if facebook.client:
            try:
                facebook.client.quit()
            except:
                pass

        await loading_message.edit_text(
            f"❌ فشل في فتح المتصفح:\n\n`{str(e)}`",
            reply_markup=keyboard,
        )


async def handle_manual_login_done(
    client: Client, callback_query: CallbackQuery, account_id: str, username: str
):
    """Handle the completion of manual login - save cookies and register account"""
    telegram_id = callback_query.from_user.id

    db: Database = client.db

    keyboard = create_keyboard(
        [
            [(ArabicText.BACK, "login:types")],
            [(ArabicText.HOME_TITLE, "home")],
        ]
    )

    # Check if we have an active session for this account
    if account_id not in active_manual_sessions:
        await callback_query.answer(
            "❌ لم يتم العثور على جلسة نشطة لهذا الحساب", show_alert=True
        )
        await callback_query.edit_message_text(
            "❌ انتهت صلاحية الجلسة أو تم إغلاقها.\n" "الرجاء البدء من جديد.",
            reply_markup=keyboard,
        )
        return

    session = active_manual_sessions[account_id]

    # Verify the session belongs to this user
    if session["telegram_id"] != telegram_id:
        await callback_query.answer("❌ هذه الجلسة لا تخصك", show_alert=True)
        return

    facebook: FacebookUtils = session["facebook"]
    email = session["email"]
    account_proxy = session["proxy"]

    # Show loading status
    await callback_query.edit_message_text(
        "⏳ جاري حفظ الجلسة...",
    )

    try:
        # Check if login was successful by checking current URL
        current_url = facebook.client.current_url

        if "login" in current_url.lower() or "checkpoint" in current_url.lower():
            # Still on login page or checkpoint
            await callback_query.edit_message_text(
                "⚠️ يبدو أن تسجيل الدخول لم يكتمل بعد.\n"
                "الرجاء إتمام تسجيل الدخول في المتصفح ثم المحاولة مرة أخرى.",
                reply_markup=create_keyboard(
                    [
                        [("✅ تم / حفظ الجلسة", f"login:manual_done:{account_id}")],
                        [(ArabicText.CANCEL, f"login:manual_cancel:{account_id}")],
                    ]
                ),
            )
            return

        # Take a screenshot for verification
        screenshot_path = None
        try:
            os.makedirs("screenshots", exist_ok=True)
            screenshot_path = f"screenshots/{uuid.uuid4().hex}.png"
            facebook.client.save_screenshot(screenshot_path)
        except Exception as e:
            print(f"Warning: Failed to take screenshot: {e}")

        # Save cookies
        cookies_file = os.path.join("cookies", f"{email}.json")
        os.makedirs("cookies", exist_ok=True)
        cookies_saved = facebook.save_cookies(cookies_file)

        if not cookies_saved:
            await callback_query.edit_message_text(
                "❌ فشل في حفظ الكوكيز. الرجاء المحاولة مرة أخرى.",
                reply_markup=keyboard,
            )
            return

        # Add or update Facebook account in database with auto-assigned proxy
        db.add_facebook_account(
            email=email, cookies_path=cookies_file, proxy=account_proxy
        )

        # Add Facebook account to user if not already added
        db.add_facebook_account_to_user(username, email)

        # Close the browser
        try:
            facebook.client.quit()
        except:
            pass

        # Remove from active sessions
        del active_manual_sessions[account_id]

        # Send success message with screenshot if available
        if screenshot_path and os.path.exists(screenshot_path):
            with open(screenshot_path, "rb") as f:
                screenshot_bytes = BytesIO(f.read())
                screenshot_bytes.name = os.path.basename(screenshot_path)

            await callback_query.message.reply_photo(
                photo=screenshot_bytes,
                caption=f"✅ **تم تسجيل الدخول وحفظ الجلسة بنجاح!**\n\n"
                f"📧 الحساب: `{email}`\n"
                f"🔐 تم حفظ الكوكيز",
                reply_markup=keyboard,
            )

            # Clean up screenshot
            try:
                os.remove(screenshot_path)
            except:
                pass

            # Delete the original message
            try:
                await callback_query.message.delete()
            except:
                pass
        else:
            await callback_query.edit_message_text(
                f"✅ **تم تسجيل الدخول وحفظ الجلسة بنجاح!**\n\n"
                f"📧 الحساب: `{email}`\n"
                f"🔐 تم حفظ الكوكيز",
                reply_markup=keyboard,
            )

    except Exception as e:
        # Clean up on error
        try:
            facebook.client.quit()
        except:
            pass

        # Remove from active sessions
        if account_id in active_manual_sessions:
            del active_manual_sessions[account_id]

        await callback_query.edit_message_text(
            f"❌ حدث خطأ أثناء حفظ الجلسة:\n\n`{str(e)}`",
            reply_markup=keyboard,
        )


async def handle_manual_login_cancel(client: Client, callback_query: CallbackQuery):
    """Handle cancellation of manual login"""
    data = callback_query.data.split(":")
    if len(data) < 3:
        return

    account_id = data[2]
    telegram_id = callback_query.from_user.id

    keyboard = create_keyboard(
        [
            [(ArabicText.BACK, "login:types")],
            [(ArabicText.HOME_TITLE, "home")],
        ]
    )

    # Check if we have an active session for this account
    if account_id in active_manual_sessions:
        session = active_manual_sessions[account_id]

        # Verify the session belongs to this user
        if session["telegram_id"] != telegram_id:
            await callback_query.answer("❌ هذه الجلسة لا تخصك", show_alert=True)
            return

        facebook: FacebookUtils = session["facebook"]

        # Close the browser
        try:
            facebook.client.quit()
        except:
            pass

        # Remove from active sessions
        del active_manual_sessions[account_id]

    await callback_query.edit_message_text(
        "تم إلغاء العملية.",
        reply_markup=keyboard,
    )
