from typing import Any, Dict, List, Tuple, Union

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


class ArabicText:
    """Text constants in Arabic"""

    # Start
    WELCOME = "مرحباً بك في بوت فيسبوك! يمكنك إدارة حساباتك المضافة من هنا."

    # Login
    LOGIN_TITLE = "تسجيل الدخول إلى فيسبوك"
    LOGIN_WITH_CREDENTIALS = "[ Password ]"
    LOGIN_WITH_COOKIES = "[ Cookies ]"
    LOGIN_WITH_COOKIES_FILE = "ملف كوكيز (.json)"
    LOGIN_WITH_COOKIES_STR = "نص (email:cookies_str)"
    ENTER_EMAIL = "الرجاء إدخال بريدك الإلكتروني:"
    ENTER_PASSWORD = "الرجاء إدخال كلمة المرور لحساب {email}:"
    ENTER_COOKIES_STR = "الرجاء إدخال نص الكوكيز بالتنسيق التالي:\nemail:cookies_str"
    LOGIN_SUCCESS = "تم تسجيل الدخول بنجاح إلى حساب {email}"
    LOGIN_FAILED = "فشل تسجيل الدخول: \n\nError: {error}\nError type: {error_type}"
    LOADING = "جاري التحميل..."
    VERIFY_LOGIN = "هل نجح تسجيل الدخول؟ الرجاء التحقق من الصورة أدناه:"
    LOGIN_VERIFIED = "تم التحقق من نجاح تسجيل الدخول و اضافة الحساب"
    LOGIN_NOT_VERIFIED = "لم ينجح تسجيل الدخول، الرجاء المحاولة مرة أخرى"

    # Logout
    USER_LOGOUT_SUCCESS = "تم تسجيل الخروج من حساب {username}"
    USER_LOGOUT_FAILED = "فشل تسجيل الخروج: {error}"

    # Accounts
    ACCOUNTS_TITLE = "إدارة الحسابات"
    LIST_ACCOUNTS = "عرض الحسابات"
    SELECT_ACCOUNT = "الرجاء اختيار حساب فيسبوك:"
    ADD_ACCOUNT = "إضافة حساب جديد"
    NO_ACCOUNTS = "ليس لديك أي حسابات فيسبوك مضافة بعد. الرجاء إضافة حساب جديد:"
    ACCOUNT_NOT_FOUND = "الحساب غير موجود"
    NOT_ACCOUNT_OWNER = "أنت لست مالك هذا الحساب"

    # Services
    SERVICES_TITLE = "الخدمات المتاحة"
    SERVICES = "اختر الخدمة التي تريد استخدامها:"
    LIKE_SERVICE = "الإعجاب بمنشور 👍"
    COMMENT_SERVICE = "التعليق على منشور 💬"
    FOLLOW_SERVICE = "متابعة صفحة 🔔"
    SHARE_SERVICE = "مشاركة منشور 🔄"

    ENTER_POST_URL = "أدخل رابط المنشور:"
    ENTER_PAGE_URL = "أدخل رابط الصفحة أو الملف الشخصي:"
    ENTER_COMMENT_TEXT = "أدخل نص التعليق:"
    ENTER_SHARE_TEXT = "أدخل نص المشاركة (اختياري):"
    INVALID_URL = "الرابط غير صالح، الرجاء التأكد من إدخال رابط صحيح"
    INPUT_TIMEOUT = "انتهت مهلة الاستلام الرجاء المحاولة مرة أخرى"
    SELECT_ACCOUNTS_COUNT = "لديك {count} حساب/حسابات. كم حساب تريد استخدام؟\n\nأرسل رقم من 1 إلى {count} أو أرسل 'الكل' لاستخدام جميع الحسابات"
    # SELECT_SHARE_VISIBILITY = "اختر خصوصية المشاركة:"
    # SHARE_PUBLIC = "عام 🌍"
    # SHARE_FRIENDS = "الأصدقاء 👥"
    # SHARE_ONLY_ME = "أنا فقط 🔒"

    # Help
    HELP_TITLE = "المساعدة"

    # Navigation
    HOME_TITLE = "الصفحة الرئيسية"
    BACK = "رجوع"
    CANCEL = "إلغاء"

    # Admin
    ADD_USER = "إضافة مستخدم"
    REMOVE_USER = "حذف مستخدم"
    ERROR_NOT_AUTHORIZED = "غير مصرح لك باستخدام هذا الأمر"

    # General
    YES = "نعم ✅"
    NO = "لا ❌"
    SUCCESS = "تم بنجاح"
    ERROR = "حدث خطأ"
    ERROR_RELOGIN = "إعادة تسجيل الدخول"
    DELETE = "حذف"
    EDIT = "تعديل"
    PREVIOUS_PAGE = "الصفحة السابقة"
    NEXT_PAGE = "الصفحة التالية"

    # Account Check
    CHECK_ACCOUNT = "فحص 🔍"
    ACCOUNT_CHECK_SUCCESS = "تم فحص الحساب بنجاح ✅"
    ACCOUNT_CHECK_FAILED = "فشل الفحص ❌"
    ACCOUNT_CHECK_LOADING = "جاري فحص الحساب..."
    ACCOUNT_CHECK_RESULT = "نتيجة فحص الحساب"
    ACCOUNT_CHECK_RELOGIN = "إعادة تسجيل الدخول"
    RELOGIN_METHOD = "اختر طريقة تسجيل الدخول مجدداً:"
    
    # Relogin
    RELOGIN_BUTTON = "إعادة تسجيل"
    RELOGIN_CONFIRM_TITLE = "⚠️ تأكيد إعادة تسجيل الدخول"
    RELOGIN_CONFIRM_MESSAGE = (
        "⚠️ **تحذير هام:**\n\n"
        "إعادة تسجيل الدخول ستقوم بـ:\n"
        "• حذف جلسة تسجيل الدخول الحالية\n"
        "📧 الحساب: `{email}`\n\n"
        "هل أنت متأكد من المتابعة؟"
    )
    RELOGIN_CANCELLED = "تم إلغاء عملية إعادة تسجيل الدخول"
    RELOGIN_PROFILE_DELETED = "✅ تم حذف البروفايل القديم"


def create_keyboard(buttons: List[List[Tuple[str, str]]]) -> InlineKeyboardMarkup:
    """Create an inline keyboard

    Args:
        buttons (List[List[Tuple[str, str]]]): List of (text, callback_data) tuples

    Returns:
        InlineKeyboardMarkup: Inline keyboard markup
    """
    keyboard = []
    for row in buttons:
        keyboard_row = []
        for text, callback_data in row:
            keyboard_row.append(
                InlineKeyboardButton(text=text, callback_data=callback_data)
            )
        keyboard.append(keyboard_row)
    return InlineKeyboardMarkup(keyboard)
