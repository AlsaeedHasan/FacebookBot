import os
from io import BytesIO
import shutil
from typing import Union

from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message

from database.database import Database
from handlers.login import login_with_credentials
from utils.facebook_utils import FacebookUtils
from utils.telegram_utils import ArabicText, create_keyboard


@Client.on_message(filters.command("accounts"))
async def accounts_command(client: Client, message: Message):
    """Handle /accounts command"""
    # Get user info
    telegram_id = message.from_user.id

    # Check if user is authenticated
    db: Database = client.db
    if not db.is_authenticated(telegram_id):
        # User is not authenticated, show error
        await message.reply(
            "يجب تسجيل الدخول أولاً لإدارة الحسابات",
            reply_markup=create_keyboard(
                [
                    [(ArabicText.HOME_TITLE, "home")],
                ]
            ),
            quote=True,
        )
        return

    # Show accounts management menu
    await accounts_menu(client, message)


@Client.on_callback_query(filters.regex(r"^(accounts:)"))
async def accounts_callback(client: Client, callback_query: CallbackQuery):
    """Handle accounts callbacks"""
    # Parse callback data
    data = callback_query.data.split(":")

    if len(data) < 2 or data[0] != "accounts":
        return

    action = data[1]

    # Check if user is authenticated
    telegram_id = callback_query.from_user.id
    db: Database = client.db

    if not db.is_authenticated(telegram_id):
        await callback_query.answer("يجب تسجيل الدخول أولاً", show_alert=True)
        return

    # Get authenticated username
    username = db.get_authenticated_username(telegram_id)

    if action == "menu" or action == "":
        # Show accounts menu
        await accounts_menu(client, callback_query, is_callback=True)
    elif action == "list":
        # List accounts
        await list_accounts(client, callback_query, username)
    elif action == "delete":
        # Delete account
        if len(data) < 3:
            await callback_query.answer("حدث خطأ", show_alert=True)
            return

        email = data[2]

        # Check if user is account owner
        if not db.is_facebook_account_owner(username, email):
            await callback_query.answer("أنت لست مالك هذا الحساب", show_alert=True)
            return

        # Delete account
        db.remove_facebook_account(email)
        shutil.rmtree(
            f"./profiles/{email.replace('@', '_').replace('.', '_')}",
            ignore_errors=True,
        )

        await callback_query.answer("تم حذف الحساب بنجاح", show_alert=True)
        await accounts_menu(client, callback_query, is_callback=True)
    elif action == "check":
        # Check if user is authenticated
        if not db.is_authenticated(telegram_id):
            await callback_query.answer("يجب تسجيل الدخول أولاً", show_alert=True)
            return

        # Get authenticated username
        username = db.get_authenticated_username(telegram_id)

        if len(data) < 3:
            await callback_query.answer("حدث خطأ", show_alert=True)
            return

        email = data[2]

        # Check if user is account owner
        if not db.is_facebook_account_owner(username, email):
            await callback_query.answer("أنت لست مالك هذا الحساب", show_alert=True)
            return

        # Get account info
        account = db.get_facebook_account(email)
        if not account:
            await callback_query.answer(ArabicText.ACCOUNT_NOT_FOUND, show_alert=True)
            return

        # Show loading message
        await callback_query.edit_message_text(ArabicText.ACCOUNT_CHECK_LOADING)

        # Check account
        facebook = FacebookUtils()
        result, screenshot = facebook.check_account(
            email, cookies_file=account["cookies_path"]
        )

        if result["status"] == "ok":
            # Account is still valid
            with open(screenshot, "rb") as f:
                bytes = f.read()
                bscreenshot = BytesIO(bytes)
                bscreenshot.name = os.path.basename(screenshot)
            screenshot_message = await callback_query.message.reply_photo(
                photo=screenshot,
                caption=f"{ArabicText.ACCOUNT_CHECK_SUCCESS}\n\nEmail: {email}",
                reply_markup=create_keyboard(
                    [
                        [(ArabicText.BACK, "accounts:menu")],
                        [(ArabicText.HOME_TITLE, "home")],
                    ]
                ),
            )
            if os.path.exists(screenshot):
                os.remove(screenshot)
        else:
            # Account needs relogin
            keyboard = create_keyboard(
                [
                    [
                        (
                            ArabicText.LOGIN_WITH_COOKIES,
                            f"accounts:check_relogin:cookies:{email}",
                        ),
                        (
                            ArabicText.LOGIN_WITH_CREDENTIALS,
                            f"accounts:check_relogin:password:{email}",
                        ),
                    ],
                    [(ArabicText.BACK, "accounts:menu")],
                    [(ArabicText.HOME_TITLE, "home")],
                ]
            )
            await callback_query.message.reply_photo(
                photo=screenshot,
                caption=f"{ArabicText.ACCOUNT_CHECK_FAILED}\n\n"
                f"Email: {email}\n"
                f"Error: {result.get('message', 'None')}\n"
                f"{ArabicText.RELOGIN_METHOD}",
                reply_markup=keyboard,
            )
            if os.path.exists(screenshot):
                os.remove(screenshot)

        facebook.close()
        await callback_query.message.delete()

    elif action == "check_relogin":
        if len(data) < 4:
            await callback_query.answer("حدث خطأ", show_alert=True)
            return

        relogin_type = data[2]  # cookies or password
        email = data[3]

        if relogin_type == "cookies":
            await callback_query.edit_message_text(
                ArabicText.LOGIN_WITH_COOKIES,
                reply_markup=create_keyboard(
                    [
                        [
                            (ArabicText.LOGIN_WITH_COOKIES_FILE, f"login:cookies:file"),
                            (ArabicText.LOGIN_WITH_COOKIES_STR, f"login:cookies:str"),
                        ],
                        [(ArabicText.BACK, f"accounts:check:{email}")],
                        [(ArabicText.HOME_TITLE, "home")],
                    ]
                ),
            )
        elif relogin_type == "password":
            await login_with_credentials(client, callback_query, username)


@Client.on_callback_query(filters.regex(r"^(accounts)$"))
async def accounts_main_callback(client: Client, callback_query: CallbackQuery):
    """Handle main accounts callback"""
    await callback_query.answer()
    await accounts_menu(client, callback_query, is_callback=True)


async def accounts_menu(
    client: Client, update: Union[Message, CallbackQuery], is_callback: bool = False
):
    """Show accounts menu"""
    # Check if user is authenticated
    telegram_id = update.from_user.id
    db: Database = client.db

    if not db.is_authenticated(telegram_id):
        # User is not authenticated, show error
        error_message = "يجب تسجيل الدخول أولاً لإدارة الحسابات"
        keyboard = create_keyboard(
            [
                [(ArabicText.HOME_TITLE, "home")],
            ]
        )
        if is_callback:
            await update.answer(error_message, show_alert=True)
        else:
            await update.edit(
                error_message,
                reply_markup=keyboard,
            )
        return

    # Get authenticated username
    username = db.get_authenticated_username(telegram_id)

    # Show accounts menu
    accounts_text = ArabicText.ACCOUNTS_TITLE

    keyboard = [
        [
            (ArabicText.ADD_ACCOUNT, "login:types"),
            (ArabicText.LIST_ACCOUNTS, "accounts:list"),
        ],
        [(ArabicText.HOME_TITLE, "home")],
    ]

    if is_callback:
        await update.edit_message_text(
            accounts_text, reply_markup=create_keyboard(keyboard)
        )
    else:
        await update.reply(
            accounts_text, reply_markup=create_keyboard(keyboard), quote=True
        )


async def list_accounts(
    client: Client, update: Union[Message, CallbackQuery], username: str, start: int = 0
):
    """List accounts for a user"""
    # Get user's accounts
    db: Database = client.db
    accounts = db.get_bot_user_facebook_accounts(username)

    if not accounts:
        # User has no accounts
        await update.answer("لا توجد حسابات مضافة", show_alert=True)
        return

    # Pagination settings
    page_size = 10
    end = start + page_size
    paginated_accounts = accounts[start:end]

    # Build list of accounts
    accounts_text = "الحسابات المضافة:\n\n"

    keyboard = []
    keyboard.append(
        [(ArabicText.ADD_ACCOUNT, "accounts:add")],
    )

    for i, email in enumerate(paginated_accounts, start + 1):
        account_info = db.get_facebook_account(email)
        if not account_info:
            continue

        accounts_text += (
            f"{i}. {email}\n"  # Add account to keyboard with check and delete options
        )
        keyboard.extend(
            [
                [(email.split("@")[0], email)],
                [
                    (ArabicText.CHECK_ACCOUNT, f"accounts:check:{email}"),
                    (f"🗑️ حذف", f"accounts:delete:{email}"),
                ],
            ]
        )

    # Add navigation buttons
    if start > 0:
        keyboard.append(
            [(ArabicText.PREVIOUS_PAGE, f"accounts:list:{start - page_size}")]
        )
    if end < len(accounts):
        keyboard.append([(ArabicText.NEXT_PAGE, f"accounts:list:{end}")])

    keyboard.extend(
        [
            [(ArabicText.BACK, "accounts:menu")],
            [(ArabicText.HOME_TITLE, "home")],
        ]
    )
    await update.edit_message_text(
        accounts_text, reply_markup=create_keyboard(keyboard)
    )
