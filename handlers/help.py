from typing import Union

from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message

from utils.telegram_utils import ArabicText, create_keyboard


@Client.on_message(filters.command("help"))
@Client.on_callback_query(filters.regex(r"^(help)$"))
async def help(client: Client, update: Union[Message, CallbackQuery]):
    """Handle /help command"""
    await send_help_message(client, update, isinstance(update, CallbackQuery))


async def send_help_message(
    client: Client, update: Union[CallbackQuery, Message], is_callback: bool = False
):
    """Send help message"""
    help_text = (
        "🔹 **مرحباً بك في بوت إدارة حسابات فيسبوك** 🔹\n\n"
        "يمكنك استخدام البوت للقيام بالعديد من العمليات على حساباتك في فيسبوك:\n\n"
        "📌 **الأوامر المتاحة:**\n"
        "/start - بدء استخدام البوت\n"
        "/login - تسجيل الدخول إلى حساب فيسبوك\n"
        "/accounts - إدارة حساباتك\n"
        "/services - عرض الخدمات المتاحة\n"
        "/help - عرض هذه المساعدة\n\n"
        "🔐 **تسجيل الدخول:**\n"
        "يمكنك تسجيل الدخول إلى حساب فيسبوك بإحدى الطرق التالية:\n"
        "- باستخدام البريد الإلكتروني وكلمة المرور (غير موصى به)\n"
        "- باستخدام ملف الكوكيز (.json)\n"
        "- باستخدام نص الكوكيز (email:cookies_str)\n\n"
        "🛠 **الخدمات المتاحة:**\n"
        "بعد تسجيل الدخول، يمكنك استخدام العديد من الخدمات على حسابك."
    )

    keyboard = create_keyboard([[(ArabicText.HOME_TITLE, "home")]])

    if is_callback:
        await update.edit_message_text(help_text, reply_markup=keyboard)
    else:
        await update.reply(help_text, reply_markup=keyboard, quote=True)
