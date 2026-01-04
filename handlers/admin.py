from pyrogram import Client, filters
from pyrogram.errors import ListenerStopped, ListenerTimeout
from pyrogram.types import CallbackQuery, Message

from database.database import Database
from utils.telegram_utils import ArabicText, create_keyboard

# Store temporary admin data
admin_data = {}


def superuser_only(func):
    """Decorator to restrict commands to superuser only"""

    async def wrapper(client, message_or_callback, *args, **kwargs):
        # Get user ID
        if isinstance(message_or_callback, CallbackQuery):
            telegram_id = message_or_callback.from_user.id
            is_callback = True
        else:  # Message
            telegram_id = message_or_callback.from_user.id
            is_callback = False

        # Check if user is superuser
        db: Database = client.db
        if db.is_superuser(telegram_id):
            return await func(client, message_or_callback, *args, **kwargs)
        else:
            if is_callback:
                await message_or_callback.answer(
                    ArabicText.ERROR_NOT_AUTHORIZED, show_alert=True
                )
            else:
                await message_or_callback.reply(ArabicText.ERROR_NOT_AUTHORIZED)
            return None

    return wrapper


@Client.on_message(filters.command("admin"))
@superuser_only
async def admin(client: Client, message: Message):
    """Handle /admin command"""
    # Show admin menu
    keyboard = create_keyboard(
        [
            [
                (ArabicText.ADD_USER, "admin:add_user"),
                (ArabicText.REMOVE_USER, "admin:remove_user"),
            ],
            [(ArabicText.HOME_TITLE, "home")],
        ]
    )

    await message.reply("قائمة المشرف", reply_markup=keyboard, quote=True)


@Client.on_callback_query(filters.regex(r"^(admin:)"))
@superuser_only
async def admin_callback(client: Client, callback_query: CallbackQuery):
    """Handle admin callback"""
    # Parse callback data
    data = callback_query.data.split(":")

    if len(data) < 2 or data[0] != "admin":
        return

    action = data[1]
    telegram_id = callback_query.from_user.id

    # Get database
    db: Database = client.db

    keyboard = create_keyboard([[(ArabicText.HOME_TITLE, "home")]])

    if action == "add_user":
        # Ask for username

        username_prompt = await callback_query.edit_message_text(
            "أدخل اسم المستخدم الذي تريد إضافته:"
        )

        try:
            # Wait for username input
            username_response: Message = await client.listen(
                filters.text, user_id=telegram_id, chat_id=telegram_id, timeout=60
            )
        except (ListenerTimeout, ListenerStopped):
            # Timeout occurred
            await password_prompt.reply(
                "انتهت مهلة إدخال كلمة المرور. يرجى المحاولة مرة أخرى.",
                reply_markup=keyboard,
                quote=True,
            )
        # Check if user clicked cancel
        if username_response.text == "/cancel":
            await username_response.reply(
                "تم إلغاء العملية", quote=True, reply_markup=keyboard
            )
            return

        # Get username
        username = username_response.text

        # Check if username already exists
        if db.get_bot_user(username) or username == db.data["superuser"]["username"]:
            await username_response.reply(
                "اسم المستخدم موجود بالفعل. الرجاء اختيار اسم آخر.",
                reply_markup=keyboard,
                quote=True,
            )
            return

        # Ask for password
        password_prompt: Message = await username_response.reply(
            f"أدخل كلمة المرور للمستخدم {username}:",
            reply_markup=keyboard,
            quote=True,
        )

        try:
            # Wait for password input
            password_response: Message = await client.listen(
                filters.text, user_id=telegram_id, chat_id=telegram_id, timeout=60
            )
        except (ListenerTimeout, ListenerStopped):
            # Timeout occurred
            await username_prompt.reply(
                "انتهت مهلة إدخال اسم المستخدم. يرجى المحاولة مرة أخرى.",
                reply_markup=keyboard,
                quote=True,
            )

        # Check if user clicked cancel
        if password_response.text == "/cancel":
            await password_response.reply(
                "تم إلغاء العملية", reply_markup=keyboard, quote=True
            )
            return

        # Delete password message for security
        await password_response.delete()

        # Get password
        password = password_response.text

        # Add user to database
        if db.add_bot_user(username, password, is_admin=False):
            await password_prompt.edit(
                "تم إضافة المستخدم بنجاح ✅",
                reply_markup=keyboard,
            )
        else:
            await password_prompt.reply(
                "حدث خطأ أثناء إضافة المستخدم ❌",
                reply_markup=keyboard,
                quote=True,
            )

    elif action == "remove_user" and len(data) == 2:
        # Get all bot users
        all_users = db.get_all_bot_users()

        if all_users:
            # Show users to remove
            buttons = []
            for username in all_users.keys():
                buttons.append([(username, f"admin:remove_user:{username}")])

            buttons.append([(ArabicText.CANCEL, "home")])

            keyboard = create_keyboard(buttons)

            await callback_query.edit_message_text(
                "اختر المستخدم الذي تريد حذفه:", reply_markup=keyboard
            )
        else:
            # No users to remove
            await callback_query.answer("لا يوجد مستخدمين لحذفهم", show_alert=True)

    elif action == "remove_user" and len(data) > 2:
        # Remove specific user
        target_username = data[2]

        # Remove user
        db.remove_bot_user(target_username)

        await callback_query.answer("تم حذف المستخدم بنجاح", show_alert=True)

        # Show admin menu
        keyboard = create_keyboard(
            [
                [
                    (ArabicText.ADD_USER, "admin:add_user"),
                    (ArabicText.REMOVE_USER, "admin:remove_user"),
                ],
                [(ArabicText.HOME_TITLE, "home")],
            ]
        )

        await callback_query.edit_message_text(
            "تم حذف المستخدم بنجاح", reply_markup=keyboard
        )
