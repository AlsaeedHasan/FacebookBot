from typing import Dict, List, Union

from pyrogram import Client, filters
from pyrogram.errors import ListenerStopped, ListenerTimeout
from pyrogram.types import CallbackQuery, Message

from database.database import Database
from utils import ArabicText, create_keyboard


@Client.on_message(filters.command("start") & filters.private)
@Client.on_callback_query(filters.regex(r"^(start)"))
async def start(client: Client, message: Union[Message, CallbackQuery]):
    """Handle /start command"""
    # Get user info
    telegram_id = message.from_user.id

    # Check if user is already authenticated
    db: Database = client.db
    if db.is_authenticated(telegram_id):
        # User is already authenticated, show home screen
        await home(client, message)
        return

    # User is not authenticated, show available bot accounts to login
    # Get all bot users
    bot_users: Dict[str, Dict[str, str]] = db.get_all_bot_users()

    # Add superuser account
    superuser_username: str = db.data["superuser"]["username"]

    # Create buttons for all available accounts
    buttons = []

    # Add superuser button
    buttons.append([(superuser_username.capitalize(), f"auth:{superuser_username}")])

    # Add regular user buttons
    for username in bot_users.keys():
        buttons.append([(username.capitalize(), f"auth:{username}")])

    keyboard = create_keyboard(buttons)

    if isinstance(message, Message):
        await message.reply(
            ArabicText.SELECT_ACCOUNT, reply_markup=keyboard, quote=True
        )
    else:
        await message.edit_message_text(
            ArabicText.SELECT_ACCOUNT, reply_markup=keyboard
        )


@Client.on_callback_query(filters.regex(r"^(home)"))
@Client.on_message(filters.command("home"))
async def home(
    client: Client, callback_query_or_message: Union[CallbackQuery, Message]
):
    """Handle home callback or direct message"""
    # Get user info
    telegram_id = callback_query_or_message.from_user.id
    if isinstance(callback_query_or_message, CallbackQuery):
        is_callback = True
    else:  # Message
        is_callback = False

    # Check if user is authenticated
    db: Database = client.db
    if not db.is_authenticated(telegram_id):
        # User is not authenticated, redirect to start
        if is_callback:
            await callback_query_or_message.answer(
                "يجب تسجيل الدخول أولاً", show_alert=True
            )
            await start(client, callback_query_or_message.message)
        else:
            await start(client, callback_query_or_message)
        return

    # Get authenticated username
    username: str = db.get_authenticated_username(telegram_id)

    # Check if user is superuser
    is_superuser = db.is_superuser(telegram_id)

    # Create keyboard based on user role
    buttons = [
        [(ArabicText.HELP_TITLE, "help")],
        [
            (ArabicText.SERVICES_TITLE, "services:menu"),
            (ArabicText.ACCOUNTS_TITLE, "accounts:menu"),
        ],
        [("تسجيل الخروج 🚪", "auth:logout")],
    ]

    if is_superuser:
        buttons.insert(
            2,
            [
                (ArabicText.ADD_USER, "admin:add_user"),
                (ArabicText.REMOVE_USER, "admin:remove_user"),
            ],
        )

    keyboard = create_keyboard(buttons)

    welcome_message = f"{ArabicText.HOME_TITLE}\n\nمرحباً بك {username.capitalize()} 👋"

    # Edit message if it's a callback, otherwise send new message
    if is_callback:
        await callback_query_or_message.edit_message_text(
            welcome_message, reply_markup=keyboard
        )
    else:
        await callback_query_or_message.reply(
            welcome_message, reply_markup=keyboard, quote=True
        )


@Client.on_callback_query(filters.regex(r"^(auth:)"))
async def auth_callback(client: Client, callback_query: CallbackQuery):
    """Handle authentication callback"""
    # Parse callback data
    data = callback_query.data.split(":")

    if len(data) < 2 or data[0] != "auth":
        return

    action = data[1]
    telegram_id = callback_query.from_user.id
    db: Database = client.db

    if action == "logout":
        # End user session
        username = db.get_session(telegram_id)
        db.end_session(telegram_id)

        # Redirect to start
        await callback_query.answer(
            ArabicText.USER_LOGOUT_SUCCESS.format(username=username.capitalize()),
            show_alert=True,
        )
        await start(client, callback_query)
        return

    # Username authentication
    username = action

    # Ask for password
    password_prompt = await callback_query.edit_message_text(
        f"أدخل كلمة المرور لحساب {username.capitalize()}:",
    )

    try:
        # Wait for user's password input
        password_response: Message = await client.listen(
            filters.text, user_id=telegram_id, chat_id=telegram_id, timeout=60
        )

        # Check if user clicked cancel
        if password_response.text == "/cancel":
            await password_response.reply("تم إلغاء عملية تسجيل الدخول", quote=True)
            await start(client, password_response)
            return

        # Delete password message for security
        await password_response.delete()

        # Get password
        password = password_response.text

        # Authenticate user
        if db.authenticate_user(username, password):
            # Authentication successful
            # Create session
            db.create_session(telegram_id, username)

            # Send success message
            await password_prompt.edit_text("تم تسجيل الدخول بنجاح ✅")

            # Show home screen
            await home(client, password_response)

        else:
            # Authentication failed
            await password_prompt.edit_text(
                "كلمة المرور غير صحيحة ❌",
                reply_markup=create_keyboard(
                    [
                        [("إعادة المحاولة", f"auth:{username}")],
                        [(ArabicText.CANCEL, "cancel_auth")],
                    ],
                ),
            )
    except (ListenerTimeout, ListenerStopped):
        # Timeout occurred
        await password_prompt.reply(
            "انتهت مهلة إدخال كلمة المرور. يرجى المحاولة مرة أخرى.",
            reply_markup=create_keyboard(
                [
                    [("إعادة المحاولة", f"auth:{username}")],
                    [(ArabicText.CANCEL, "cancel_auth")],
                ],
            ),
        )
