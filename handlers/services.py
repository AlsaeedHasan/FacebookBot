import asyncio
import pprint
from time import sleep
from typing import Union

from pyrogram import Client, filters
from pyrogram.errors import ListenerStopped, ListenerTimeout
from pyrogram.types import CallbackQuery, InputMediaPhoto, Message

from database.database import Database
from utils.facebook_utils import FacebookUtils
from utils.telegram_utils import ArabicText, create_keyboard

# Store temporary user data
user_data = {}


@Client.on_message(filters.command("services"))
async def services_command(client: Client, message: Message):
    """Handle /services command"""
    # Get user info
    telegram_id = message.from_user.id

    # Check if user is authenticated
    db: Database = client.db
    if not db.is_authenticated(telegram_id):
        # User is not authenticated, show error
        await message.reply(
            "يجب تسجيل الدخول أولاً لاستخدام الخدمات",
            reply_markup=create_keyboard(
                [
                    [(ArabicText.HOME_TITLE, "home")],
                ]
            ),
            quote=True,
        )
        return

    # Show services menu
    await services_menu(client, message)


@Client.on_callback_query(filters.regex(r"^(services:)"))
async def services_callback(client: Client, callback_query: CallbackQuery):
    """Handle services callbacks"""
    # Parse callback data
    data = callback_query.data.split(":")

    if len(data) < 2 or data[0] != "services":
        return

    action = data[1]
    telegram_id = callback_query.from_user.id

    # Check if user is authenticated
    db: Database = client.db
    if not db.is_authenticated(telegram_id):
        await callback_query.answer("يجب تسجيل الدخول أولاً", show_alert=True)
        return

    # Get username
    username = db.get_authenticated_username(telegram_id)

    # Handle different services
    if action == "menu" or action == "":
        await services_menu(client, callback_query, is_callback=True)
    elif action == "like":
        await handle_like_service(client, callback_query, username)
    elif action == "comment":
        await handle_comment_service(client, callback_query, username)
    elif action == "follow":
        await handle_follow_service(client, callback_query, username)
    elif action == "share":
        await handle_share_service(client, callback_query, username)


async def services_menu(
    client: Client, update: Union[Message, CallbackQuery], is_callback: bool = False
):
    """Show services menu"""
    keyboard = create_keyboard(
        [
            [
                (ArabicText.LIKE_SERVICE, "services:like"),
                (ArabicText.COMMENT_SERVICE, "services:comment"),
            ],
            [
                (ArabicText.FOLLOW_SERVICE, "services:follow"),
                (ArabicText.SHARE_SERVICE, "services:share"),
            ],
            [(ArabicText.HOME_TITLE, "home")],
        ]
    )

    if is_callback:
        await update.edit_message_text(ArabicText.SERVICES, reply_markup=keyboard)
    else:
        await update.reply(ArabicText.SERVICES, reply_markup=keyboard, quote=True)


async def handle_like_service(
    client: Client, callback_query: CallbackQuery, username: str
):
    """Handle like service"""
    # Ask for post URL
    keyboard = create_keyboard(
        [
            [(ArabicText.BACK, "services:menu")],
            [(ArabicText.HOME_TITLE, "home")],
        ]
    )

    await callback_query.edit_message_text(
        ArabicText.ENTER_POST_URL,
        reply_markup=keyboard,
    )
    try:
        # Wait for URL input
        url_response: Message = await client.listen(
            filters.text, timeout=60, user_id=callback_query.from_user.id
        )
    except (ListenerTimeout, ListenerStopped):
        await callback_query.message.edit(
            ArabicText.INPUT_TIMEOUT,
            reply_markup=create_keyboard(
                [
                    [(ArabicText.BACK, "services:menu")],
                    [(ArabicText.HOME_TITLE, "home")],
                ]
            ),
        )
        return
    if url_response.text == "/cancel":
        await url_response.reply("تم إلغاء العملية", quote=True, reply_markup=keyboard)
        return

    # Validate URL
    if not is_valid_facebook_url(url_response.text):
        await url_response.reply(
            ArabicText.INVALID_URL,
            reply_markup=create_keyboard(
                [
                    [(ArabicText.BACK, "services:menu")],
                    [(ArabicText.HOME_TITLE, "home")],
                ]
            ),
            quote=True,
        )
        return

    post_url = url_response.text

    # Get user's accounts
    db: Database = client.db
    accounts = db.get_bot_user_facebook_accounts(username)

    if not accounts:
        await url_response.reply(
            ArabicText.NO_ACCOUNTS,
            reply_markup=create_keyboard(
                [
                    [(ArabicText.ADD_ACCOUNT, "login:types")],
                    [(ArabicText.HOME_TITLE, "home")],
                ]
            ),
            quote=True,
        )
        return

    # Ask how many accounts to use
    accounts_prompt = await url_response.reply(
        ArabicText.SELECT_ACCOUNTS_COUNT.format(count=len(accounts)), quote=True
    )

    # Wait for account selection
    try:
        accounts_response: Message = await client.listen(
            filters.text, timeout=60, user_id=callback_query.from_user.id
        )
    except (ListenerTimeout, ListenerStopped):
        await accounts_prompt.edit_text(
            ArabicText.INPUT_TIMEOUT,
            reply_markup=create_keyboard(
                [
                    [(ArabicText.BACK, "services:menu")],
                    [(ArabicText.HOME_TITLE, "home")],
                ]
            ),
        )
        return

    if accounts_response.text == "/cancel":
        await accounts_response.reply(
            "تم إلغاء العملية", quote=True, reply_markup=keyboard
        )
        return

    account_count = 0
    selected_accounts = []

    if accounts_response.text.lower() in ["all", "الكل"]:
        selected_accounts = accounts
    else:
        try:
            account_count = int(accounts_response.text)
            if 1 <= account_count <= len(accounts):
                selected_accounts = accounts[:account_count]
            else:
                await accounts_response.reply(
                    f"الرقم غير صالح. يجب أن يكون بين 1 و {len(accounts)}",
                    reply_markup=create_keyboard(
                        [
                            [(ArabicText.SERVICES, "services:menu")],
                            [(ArabicText.HOME_TITLE, "home")],
                        ]
                    ),
                )
                return
        except ValueError:
            await accounts_response.reply(
                "الإدخال غير صالح. يرجى إدخال رقم أو 'الكل'",
                reply_markup=create_keyboard(
                    [
                        [(ArabicText.SERVICES, "services:menu")],
                        [(ArabicText.HOME_TITLE, "home")],
                    ]
                ),
            )
            return

    # Process the like service
    status_message = await accounts_prompt.reply("جاري التنفيذ...", quote=True)
    await asyncio.create_task(
        process_like_service(
            client,
            status_message,
            post_url,
            callback_query.from_user.id,
            username,
            db,
            selected_accounts,
        )
    )


def is_valid_facebook_url(url: str, profile: bool = False) -> bool:
    """Check if URL is a valid Facebook post or profile URL"""
    import re

    patterns = [
        r"^https?:\/\/(www\.|m\.)?(facebook|fb)\.com\/([a-zA-Z0-9\.]+\/?)?(\?.*?)?(#.*)?$",  # Profile/Page URL
        r"^https?:\/\/(www\.|m\.)?(facebook|fb)\.com\/(.*?\/)?(profile\.php\?id=[0-9]+)(#.*)?$",  # Profile/Page URL with ID
        r"^https?:\/\/(www\.|m\.)?(facebook|fb)\.com\/(.*?\/)?(posts\/|story\.php|share\/p\/|permalink\.php\?story_fbid=)",  # Post URL
        r"^https?:\/\/(www\.|m\.)?(facebook|fb)\.com\/(.*?\/)?(photo|photos|media)",  # Photo URL
        r"^https?:\/\/(www\.|m\.)?(facebook|fb)\.com\/(.*?\/)?(groups\/|group)",  # Group URL
        r"^https?:\/\/(www\.|m\.)?(facebook|fb)\.com\/(.*?\/)?(events\/|event)",  # Event URL
        r"^https?:\/\/(www\.|m\.)?(facebook|fb)\.com\/(.*?\/)?(watch\/|videos\/)",  # Video URL
        r"^https?:\/\/(www\.|m\.)?(facebook|fb)\.com\/(.*?\/)?(marketplace\/|item)",  # Marketplace URL
        r"^https?:\/\/(www\.|m\.)?(facebook|fb)\.com\/(.*?\/)?(share\/)",  # Marketplace URL
    ]

    if profile:
        # Profile/Page URL pattern
        pattern = patterns[0] + "|" + patterns[1]
    else:
        # Post URL pattern
        pattern = "|".join(patterns)

    return bool(re.match(pattern, url))


async def handle_comment_service(
    client: Client, callback_query: CallbackQuery, username: str
):
    """Handle comment service"""
    # Ask for post URL
    keyboard = create_keyboard(
        [
            [(ArabicText.BACK, "services:menu")],
            [(ArabicText.HOME_TITLE, "home")],
        ]
    )

    await callback_query.edit_message_text(
        ArabicText.ENTER_POST_URL,
        reply_markup=keyboard,
    )

    try:
        # Wait for URL input
        url_response: Message = await client.listen(
            filters.text, timeout=60, user_id=callback_query.from_user.id
        )

        if url_response.text == "/cancel":
            await url_response.reply("تم إلغاء العملية", quote=True)
            return

        # Validate URL
        if not is_valid_facebook_url(url_response.text):
            await url_response.reply(
                ArabicText.INVALID_URL,
                reply_markup=create_keyboard(
                    [
                        [(ArabicText.BACK, "services:menu")],
                        [(ArabicText.HOME_TITLE, "home")],
                    ]
                ),
                quote=True,
            )
            return

        post_url = url_response.text

        # Ask for comment text
        comment_prompt = await url_response.reply(
            ArabicText.ENTER_COMMENT_TEXT,
            reply_markup=create_keyboard(
                [
                    [(ArabicText.BACK, "services:menu")],
                    [(ArabicText.HOME_TITLE, "home")],
                ]
            ),
            quote=True,
        )

        # Wait for comment input
        comment_response: Message = await client.listen(
            filters.text, timeout=60, user_id=callback_query.from_user.id
        )

        if comment_response.text == "/cancel":
            await comment_response.reply("تم إلغاء العملية", quote=True)
            return

        comment_text = comment_response.text

        # Get user's accounts
        db: Database = client.db
        accounts = db.get_bot_user_facebook_accounts(username)

        if not accounts:
            await comment_response.reply(
                ArabicText.NO_ACCOUNTS,
                reply_markup=create_keyboard(
                    [
                        [(ArabicText.ADD_ACCOUNT, "login:types")],
                        [(ArabicText.HOME_TITLE, "home")],
                    ]
                ),
                quote=True,
            )
            return

        # Ask how many accounts to use
        accounts_prompt = await comment_response.reply(
            ArabicText.SELECT_ACCOUNTS_COUNT.format(count=len(accounts)), quote=True
        )

        # Wait for account selection

        accounts_response: Message = await client.listen(
            filters.text, timeout=60, user_id=callback_query.from_user.id
        )

        if accounts_response.text == "/cancel":
            await accounts_response.reply(
                "تم إلغاء العملية", quote=True, reply_markup=keyboard
            )
            return

        account_count = 0
        selected_accounts = []

        if accounts_response.text.lower() in ["all", "الكل"]:
            selected_accounts = accounts
        else:
            try:
                account_count = int(accounts_response.text)
                if 1 <= account_count <= len(accounts):
                    selected_accounts = accounts[:account_count]
                else:
                    await accounts_response.reply(
                        f"الرقم غير صالح. يجب أن يكون بين 1 و {len(accounts)}",
                        reply_markup=create_keyboard(
                            [
                                [(ArabicText.SERVICES, "services:menu")],
                                [(ArabicText.HOME_TITLE, "home")],
                            ]
                        ),
                    )
                    return
            except ValueError:
                await accounts_response.reply(
                    "الإدخال غير صالح. يرجى إدخال رقم أو 'الكل'",
                    reply_markup=create_keyboard(
                        [
                            [(ArabicText.SERVICES, "services:menu")],
                            [(ArabicText.HOME_TITLE, "home")],
                        ]
                    ),
                )
                return

        # Process the comment service
        status_message = await accounts_prompt.reply("جاري التنفيذ...", quote=True)
        await asyncio.create_task(
            process_comment_service(
                client,
                status_message,
                post_url,
                comment_text,
                callback_query.from_user.id,
                username,
                db,
                selected_accounts,
            )
        )

    except (ListenerTimeout, ListenerStopped):
        await callback_query.message.edit(
            ArabicText.INPUT_TIMEOUT,
            reply_markup=create_keyboard(
                [
                    [(ArabicText.BACK, "services:menu")],
                    [(ArabicText.HOME_TITLE, "home")],
                ]
            ),
        )


async def handle_follow_service(
    client: Client, callback_query: CallbackQuery, username: str
):
    """Handle follow service"""
    # Ask for page URL
    keyboard = create_keyboard(
        [
            [(ArabicText.BACK, "services:menu")],
            [(ArabicText.HOME_TITLE, "home")],
        ]
    )

    await callback_query.edit_message_text(
        ArabicText.ENTER_PAGE_URL,
        reply_markup=keyboard,
    )

    try:
        # Wait for URL input
        url_response: Message = await client.listen(
            filters.text, timeout=60, user_id=callback_query.from_user.id
        )

        if url_response.text == "/cancel":
            await url_response.reply("تم إلغاء العملية", quote=True)
            return

        # Validate URL
        if not is_valid_facebook_url(url_response.text, profile=True):
            await url_response.reply(
                ArabicText.INVALID_URL,
                reply_markup=create_keyboard(
                    [
                        [(ArabicText.BACK, "services:menu")],
                        [(ArabicText.HOME_TITLE, "home")],
                    ]
                ),
                quote=True,
            )
            return

        page_url = url_response.text

        # Get user's accounts
        db: Database = client.db
        accounts = db.get_bot_user_facebook_accounts(username)

        if not accounts:
            await url_response.reply(
                ArabicText.NO_ACCOUNTS,
                reply_markup=create_keyboard(
                    [
                        [(ArabicText.ADD_ACCOUNT, "login:types")],
                        [(ArabicText.HOME_TITLE, "home")],
                    ]
                ),
                quote=True,
            )
            return  # Ask how many accounts to use
        accounts_prompt = await url_response.reply(
            ArabicText.SELECT_ACCOUNTS_COUNT.format(count=len(accounts)), quote=True
        )

        # Wait for account selection
        accounts_response: Message = await client.listen(
            filters.text, timeout=60, user_id=callback_query.from_user.id
        )

        if accounts_response.text == "/cancel":
            await accounts_response.reply(
                "تم إلغاء العملية", quote=True, reply_markup=keyboard
            )
            return

        account_count = 0
        selected_accounts = []

        if accounts_response.text.lower() in ["all", "الكل"]:
            selected_accounts = accounts
        else:
            try:
                account_count = int(accounts_response.text)
                if 1 <= account_count <= len(accounts):
                    selected_accounts = accounts[:account_count]
                else:
                    await accounts_response.reply(
                        f"الرقم غير صالح. يجب أن يكون بين 1 و {len(accounts)}",
                        reply_markup=create_keyboard(
                            [
                                [(ArabicText.SERVICES, "services:menu")],
                                [(ArabicText.HOME_TITLE, "home")],
                            ]
                        ),
                    )
                    return
            except ValueError:
                await accounts_response.reply(
                    "الإدخال غير صالح. يرجى إدخال رقم أو 'الكل'",
                    reply_markup=create_keyboard(
                        [
                            [(ArabicText.SERVICES, "services:menu")],
                            [(ArabicText.HOME_TITLE, "home")],
                        ]
                    ),
                )
                return

        # Process the follow service
        status_message = await accounts_prompt.reply("جاري التنفيذ...", quote=True)
        await asyncio.create_task(
            process_follow_service(
                client,
                status_message,
                page_url,
                callback_query.from_user.id,
                username,
                db,
                selected_accounts,
            )
        )

    except (ListenerTimeout, ListenerStopped):
        await callback_query.message.edit(
            ArabicText.INPUT_TIMEOUT,
            reply_markup=create_keyboard(
                [
                    [(ArabicText.BACK, "services:menu")],
                    [(ArabicText.HOME_TITLE, "home")],
                ]
            ),
        )


async def handle_share_service(
    client: Client, callback_query: CallbackQuery, username: str
):
    """Handle share service"""
    # Ask for post URL
    keyboard = create_keyboard(
        [
            [(ArabicText.BACK, "services:menu")],
            [(ArabicText.HOME_TITLE, "home")],
        ]
    )

    await callback_query.edit_message_text(
        ArabicText.ENTER_POST_URL,
        reply_markup=keyboard,
    )

    try:
        # Wait for URL input
        url_response: Message = await client.listen(
            filters.text, timeout=60, user_id=callback_query.from_user.id
        )

        if url_response.text == "/cancel":
            await url_response.reply("تم إلغاء العملية", quote=True)
            return

        # Validate URL
        if not is_valid_facebook_url(url_response.text):
            await url_response.reply(
                ArabicText.INVALID_URL,
                reply_markup=create_keyboard(
                    [
                        [(ArabicText.BACK, "services:menu")],
                        [(ArabicText.HOME_TITLE, "home")],
                    ]
                ),
                quote=True,
            )
            return

        post_url = url_response.text

        # Ask for share text (optional)
        # share_text_prompt = await url_response.reply(
        #     ArabicText.ENTER_SHARE_TEXT,
        #     reply_markup=create_keyboard(
        #         [
        #             [(ArabicText.BACK, "services:menu")],
        #             [(ArabicText.HOME_TITLE, "home")],
        #         ]
        #     ),
        #     quote=True,
        # )

        # # Wait for share text input
        # share_text_response: Message = await client.listen(
        #     filters.text, timeout=60, user_id=callback_query.from_user.id
        # )

        # if share_text_response.text == "/cancel":
        #     await share_text_response.reply("تم إلغاء العملية", quote=True)
        #     return

        # share_text = share_text_response.text

        # # Ask for visibility
        # visibility_prompt = await share_text_response.reply(
        #     ArabicText.SELECT_SHARE_VISIBILITY,
        #     reply_markup=create_keyboard(
        #         [
        #             [
        #                 (ArabicText.SHARE_PUBLIC, "share:public"),
        #                 (ArabicText.SHARE_FRIENDS, "share:friends"),
        #                 (ArabicText.SHARE_ONLY_ME, "share:only_me"),
        #             ],
        #             [(ArabicText.BACK, "services:menu")],
        #             [(ArabicText.HOME_TITLE, "home")],
        #         ]
        #     ),
        #     quote=True,
        # )

        # # Wait for visibility selection
        # visibility_response: CallbackQuery = await client.wait_for_callback_query(
        #     callback_query.from_user.id,
        #     filters=filters.regex(r"^share:(public|friends|only_me)$"),
        #     timeout=60,
        # )

        # visibility = visibility_response.data.split(":")[1]

        # Get user's accounts
        db: Database = client.db
        accounts = db.get_bot_user_facebook_accounts(username)

        if not accounts:
            await url_response.reply(
                ArabicText.NO_ACCOUNTS,
                reply_markup=create_keyboard(
                    [
                        [(ArabicText.ADD_ACCOUNT, "login:types")],
                        [(ArabicText.HOME_TITLE, "home")],
                    ]
                ),
                quote=True,
            )
            return  # Ask how many accounts to use
        accounts_prompt = await url_response.reply(
            ArabicText.SELECT_ACCOUNTS_COUNT.format(count=len(accounts)), quote=True
        )

        # Wait for account selection
        accounts_response: Message = await client.listen(
            filters.text, timeout=60, user_id=callback_query.from_user.id
        )

        if accounts_response.text == "/cancel":
            await accounts_response.reply(
                "تم إلغاء العملية", quote=True, reply_markup=keyboard
            )
            return

        account_count = 0
        selected_accounts = []

        if accounts_response.text.lower() in ["all", "الكل"]:
            selected_accounts = accounts
        else:
            try:
                account_count = int(accounts_response.text)
                if 1 <= account_count <= len(accounts):
                    selected_accounts = accounts[:account_count]
                else:
                    await accounts_response.reply(
                        f"الرقم غير صالح. يجب أن يكون بين 1 و {len(accounts)}",
                        reply_markup=create_keyboard(
                            [
                                [(ArabicText.SERVICES, "services:menu")],
                                [(ArabicText.HOME_TITLE, "home")],
                            ]
                        ),
                    )
                    return
            except ValueError:
                await accounts_response.reply(
                    "الإدخال غير صالح. يرجى إدخال رقم أو 'الكل'",
                    reply_markup=create_keyboard(
                        [
                            [(ArabicText.SERVICES, "services:menu")],
                            [(ArabicText.HOME_TITLE, "home")],
                        ]
                    ),
                )
                return

        # Process the share service
        status_message = await accounts_prompt.reply("جاري التنفيذ...", quote=True)
        await asyncio.create_task(
            process_share_service(
                client,
                status_message,
                post_url,
                # share_text,
                # visibility,
                callback_query.from_user.id,
                username,
                db,
                selected_accounts,
            )
        )

    except (ListenerTimeout, ListenerStopped):
        await callback_query.message.edit(
            ArabicText.INPUT_TIMEOUT,
            reply_markup=create_keyboard(
                [
                    [(ArabicText.BACK, "services:menu")],
                    [(ArabicText.HOME_TITLE, "home")],
                ]
            ),
        )


async def process_like_service(
    client: Client,
    status_message: Message,
    post_url: str,
    telegram_id: int,
    username: str,
    db: Database,
    selected_accounts: list = None,
):
    """Process like service with multiple accounts"""
    # Get user's Facebook accounts if not provided
    if not selected_accounts:
        selected_accounts = db.get_bot_user_facebook_accounts(username)

    if not selected_accounts:
        await status_message.edit_text(
            ArabicText.NO_ACCOUNTS,
            reply_markup=create_keyboard(
                [
                    [(ArabicText.ADD_ACCOUNT, "login:types")],
                    [(ArabicText.HOME_TITLE, "home")],
                ]
            ),
        )
        return

    # Initialize results tracking
    successful_count = 0
    failed_count = 0
    failed_accounts = []

    # Update status message to show progress
    await status_message.edit_text(
        f"جاري تنفيذ الإعجاب باستخدام {len(selected_accounts)} حساب/حسابات...\n"
        + f"0/{len(selected_accounts)} تم الانتهاء"
    )

    # Process each selected account
    screenshots = []
    for i, facebook_email in enumerate(selected_accounts, 1):
        facebook = None
        try:
            # Get account from database
            account = db.get_facebook_account(facebook_email)
            if not account:
                failed_count += 1
                failed_accounts.append(facebook_email)
                continue

            # Initialize FacebookUtils with account-specific proxy for anti-detect
            facebook = FacebookUtils(
                proxy=account.get("proxy"),
                account_id=facebook_email,
                optimize_bandwidth=True,
            )

            # Attempt to like the post
            login_result, screenshot = facebook.login(
                account["email"],
                cookies_file=account["cookies_path"],
                use_cookies=True,
                save_cookies=False,
                mobile_emulation=True,
                # headless=False,
            )
            if not login_result or login_result["status"] != "ok":
                failed_count += 1
                failed_accounts.append(facebook_email)
                if screenshot:
                    screenshots.append(screenshot)
                continue

            result, screenshot = facebook.react_post(post_url, facebook_email)

            if result.get("status") == "ok":
                successful_count += 1
            else:
                failed_count += 1
                failed_accounts.append(facebook_email)
            if screenshot:
                screenshots.append(screenshot)

            # Update progress
            await status_message.edit_text(
                f"جاري تنفيذ الإعجاب باستخدام {len(selected_accounts)} حساب/حسابات...\n"
                + f"{i}/{len(selected_accounts)} تم الانتهاء"
            )

        except Exception as e:
            failed_count += 1
            failed_accounts.append(facebook_email)
        finally:
            # Ensure driver.quit() is always called for each account
            if facebook:
                facebook.close()

    # Final report
    report = (
        f"📊 تقرير الإعجاب\n\n"
        f"🔗 الرابط: {post_url}\n\n"
        f"📈 الإحصائيات:\n"
        f"- عدد الحسابات المستخدمة: {len(selected_accounts)}\n"
        f"- نجاح: {successful_count}\n"
        f"- فشل: {failed_count}\n\n"
    )

    if failed_count > 0:
        report += "⚠️ الحسابات التي فشلت:\n"
        for account in failed_accounts:
            report += f"- {account}\n"
        report += "\nيرجى التحقق من صلاحية هذه الحسابات."

    await status_message.edit_text(
        report,
        reply_markup=create_keyboard(
            [
                [(ArabicText.BACK, "services:menu")],
                [(ArabicText.HOME_TITLE, "home")],
            ]
        ),
    )

    # try:
    #     if screenshots:
    #         chunks = [screenshots[i : i + 10] for i in range(0, len(screenshots), 10)]
    #         for chunk in chunks:
    #             await status_message.reply_media_group(chunk)
    # except TimeoutError:
    #     ...


async def process_comment_service(
    client: Client,
    status_message: Message,
    post_url: str,
    comment_text: str,
    telegram_id: int,
    username: str,
    db: Database,
    selected_accounts: list = None,
):
    """Process comment service with multiple accounts"""
    # Get user's Facebook accounts if not provided
    if not selected_accounts:
        selected_accounts = db.get_bot_user_facebook_accounts(username)

    if not selected_accounts:
        await status_message.edit_text(
            ArabicText.NO_ACCOUNTS,
            reply_markup=create_keyboard(
                [
                    [(ArabicText.ADD_ACCOUNT, "login:types")],
                    [(ArabicText.HOME_TITLE, "home")],
                ]
            ),
        )
        return

    # Initialize results tracking
    successful_count = 0
    failed_count = 0
    failed_accounts = []

    # Update status message to show progress
    await status_message.edit_text(
        f"جاري تنفيذ التعليق باستخدام {len(selected_accounts)} حساب/حسابات...\n"
        + f"0/{len(selected_accounts)} تم الانتهاء"
    )

    # Process each selected account
    screenshots = []
    for i, facebook_email in enumerate(selected_accounts, 1):
        facebook = None
        try:
            # Get account from database
            account = db.get_facebook_account(facebook_email)
            if not account:
                failed_count += 1
                failed_accounts.append(facebook_email)
                continue

            # Initialize FacebookUtils with account-specific proxy for anti-detect
            facebook = FacebookUtils(
                proxy=account.get("proxy"),
                account_id=facebook_email,
                optimize_bandwidth=True,
            )

            # Login to the account first
            login_result, screenshot = facebook.login(
                account["email"],
                cookies_file=account["cookies_path"],
                use_cookies=True,
                save_cookies=False,
                mobile_emulation=True,
                # headless=False,
            )
            if not login_result or login_result["status"] != "ok":
                failed_count += 1
                failed_accounts.append(facebook_email)
                if screenshot:
                    screenshots.append(
                        InputMediaPhoto(
                            media=screenshot, caption=f"Account: {facebook_email}"
                        )
                    )
                continue

            # Attempt to comment on the post
            result, screenshot = facebook.comment_post(post_url, comment_text)

            if result.get("status") == "ok":
                successful_count += 1
            else:
                failed_count += 1
                failed_accounts.append(facebook_email)
            if screenshot:
                screenshots.append(
                    InputMediaPhoto(
                        media=screenshot, caption=f"Account: {facebook_email}"
                    )
                )

            # Update progress
            await status_message.edit_text(
                f"جاري تنفيذ التعليق باستخدام {len(selected_accounts)} حساب/حسابات...\n"
                + f"{i}/{len(selected_accounts)} تم الانتهاء"
            )

        except Exception as e:
            failed_count += 1
            failed_accounts.append(facebook_email)
        finally:
            # Ensure driver.quit() is always called for each account
            if facebook:
                facebook.close()

    # Final report
    report = (
        f"📊 تقرير التعليق\n\n"
        f"🔗 الرابط: {post_url}\n"
        f"💬 التعليق: {comment_text}\n\n"
        f"📈 الإحصائيات:\n"
        f"- عدد الحسابات المستخدمة: {len(selected_accounts)}\n"
        f"- نجاح: {successful_count}\n"
        f"- فشل: {failed_count}\n\n"
    )

    if failed_count > 0:
        report += "⚠️ الحسابات التي فشلت:\n"
        for account in failed_accounts:
            report += f"- {account}\n"
        report += "\nيرجى التحقق من صلاحية هذه الحسابات."

    await status_message.edit_text(
        report,
        reply_markup=create_keyboard(
            [
                [(ArabicText.BACK, "services:menu")],
                [(ArabicText.HOME_TITLE, "home")],
            ]
        ),
    )

    # try:
    #     if screenshots:
    #         chunks = [screenshots[i : i + 10] for i in range(0, len(screenshots), 10)]
    #         for chunk in chunks:
    #             await status_message.reply_media_group(chunk)
    # except TimeoutError:
    #     ...


async def process_follow_service(
    client: Client,
    status_message: Message,
    page_url: str,
    telegram_id: int,
    username: str,
    db: Database,
    selected_accounts: list = None,
):
    """Process follow service with multiple accounts"""
    # Get user's Facebook accounts if not provided
    if not selected_accounts:
        selected_accounts = db.get_bot_user_facebook_accounts(username)

    if not selected_accounts:
        await status_message.edit_text(
            ArabicText.NO_ACCOUNTS,
            reply_markup=create_keyboard(
                [
                    [(ArabicText.ADD_ACCOUNT, "login:types")],
                    [(ArabicText.HOME_TITLE, "home")],
                ]
            ),
        )
        return

    # Initialize results tracking
    successful_count = 0
    failed_count = 0
    failed_accounts = []

    # Update status message to show progress
    await status_message.edit_text(
        f"جاري تنفيذ المتابعة باستخدام {len(selected_accounts)} حساب/حسابات...\n"
        + f"0/{len(selected_accounts)} تم الانتهاء"
    )
    # Process each selected account
    screenshots = []
    for i, facebook_email in enumerate(selected_accounts, 1):
        facebook = None
        try:
            # Get account from database
            account = db.get_facebook_account(facebook_email)
            if not account:
                failed_count += 1
                failed_accounts.append(facebook_email)
                continue

            # Initialize FacebookUtils with account-specific proxy for anti-detect
            facebook = FacebookUtils(
                proxy=account.get("proxy"),
                account_id=facebook_email,
                optimize_bandwidth=True,
            )

            # Login to the account first
            login_result, screenshot = facebook.login(
                account["email"],
                cookies_file=account["cookies_path"],
                use_cookies=True,
                save_cookies=False,
                mobile_emulation=True,
            )
            if not login_result or login_result["status"] != "ok":
                failed_count += 1
                failed_accounts.append(facebook_email)
                continue

            # Attempt to follow the page
            result, screenshot = facebook.follow_page(page_url)

            if result.get("status") == "ok":
                successful_count += 1
            else:
                failed_count += 1
                failed_accounts.append(facebook_email)
            if screenshot:
                screenshots.append(screenshot)

            # Update progress
            await status_message.edit_text(
                f"جاري تنفيذ المتابعة باستخدام {len(selected_accounts)} حساب/حسابات...\n"
                + f"{i}/{len(selected_accounts)} تم الانتهاء"
            )

        except Exception as e:
            failed_count += 1
            failed_accounts.append(facebook_email)
        finally:
            # Ensure driver.quit() is always called for each account
            if facebook:
                facebook.close()

    # Final report
    report = (
        f"📊 تقرير المتابعة\n\n"
        f"🔗 الرابط: {page_url}\n\n"
        f"📈 الإحصائيات:\n"
        f"- عدد الحسابات المستخدمة: {len(selected_accounts)}\n"
        f"- نجاح: {successful_count}\n"
        f"- فشل: {failed_count}\n\n"
    )

    if failed_count > 0:
        report += "⚠️ الحسابات التي فشلت:\n"
        for account in failed_accounts:
            report += f"- {account}\n"
        report += "\nيرجى التحقق من صلاحية هذه الحسابات."

    await status_message.edit_text(
        report,
        reply_markup=create_keyboard(
            [
                [(ArabicText.BACK, "services:menu")],
                [(ArabicText.HOME_TITLE, "home")],
            ]
        ),
    )

    # try:
    #     if screenshots:
    #         chunks = [screenshots[i : i + 10] for i in range(0, len(screenshots), 10)]
    #         for chunk in chunks:
    #             await status_message.reply_media_group(chunk)
    # except TimeoutError:
    #     ...


async def process_share_service(
    client: Client,
    status_message: Message,
    post_url: str,
    # share_text: str,
    telegram_id: int,
    username: str,
    db: Database,
    selected_accounts: list = None,
):
    """Process share service with multiple accounts"""
    # Get user's Facebook accounts if not provided
    if not selected_accounts:
        selected_accounts = db.get_bot_user_facebook_accounts(username)

    if not selected_accounts:
        await status_message.edit_text(
            ArabicText.NO_ACCOUNTS,
            reply_markup=create_keyboard(
                [
                    [(ArabicText.ADD_ACCOUNT, "login:types")],
                    [(ArabicText.HOME_TITLE, "home")],
                ]
            ),
        )
        return

    # Initialize results tracking
    successful_count = 0
    failed_count = 0
    failed_accounts = []

    # Update status message to show progress
    await status_message.edit_text(
        f"جاري تنفيذ المشاركة باستخدام {len(selected_accounts)} حساب/حسابات...\n"
        + f"0/{len(selected_accounts)} تم الانتهاء"
    )
    # Process each selected account
    screenshots = []
    for i, facebook_email in enumerate(selected_accounts, 1):
        facebook = None
        try:
            # Get account from database
            account = db.get_facebook_account(facebook_email)
            if not account:
                failed_count += 1
                failed_accounts.append(facebook_email)
                continue

            # Initialize FacebookUtils with account-specific proxy for anti-detect
            facebook = FacebookUtils(
                proxy=account.get("proxy"),
                account_id=facebook_email,
                optimize_bandwidth=True,
            )

            # Login to the account first
            login_result, screenshot = facebook.login(
                account["email"],
                cookies_file=account["cookies_path"],
                use_cookies=True,
                save_cookies=False,
                mobile_emulation=True,
            )
            if not login_result or login_result["status"] != "ok":
                failed_count += 1
                failed_accounts.append(facebook_email)
                continue

            # Attempt to share the post
            result, screenshot = facebook.share_post(post_url)

            if result.get("status") == "ok":
                successful_count += 1
            else:
                failed_count += 1
                failed_accounts.append(facebook_email)

            if screenshot:
                screenshots.append(screenshot)

            # Update progress
            await status_message.edit_text(
                f"جاري تنفيذ المشاركة باستخدام {len(selected_accounts)} حساب/حسابات...\n"
                + f"{i}/{len(selected_accounts)} تم الانتهاء"
            )

        except Exception as e:
            failed_count += 1
            failed_accounts.append(facebook_email)
        finally:
            # Ensure driver.quit() is always called for each account
            if facebook:
                facebook.close()

    # Final report
    report = (
        f"📊 تقرير المشاركة\n\n"
        f"🔗 الرابط: {post_url}\n"
        # f"📝 النص: {share_text}\n"
        # f"👀 الخصوصية: {visibility}\n\n"
        f"📈 الإحصائيات:\n"
        f"- عدد الحسابات المستخدمة: {len(selected_accounts)}\n"
        f"- نجاح: {successful_count}\n"
        f"- فشل: {failed_count}\n\n"
    )

    if failed_count > 0:
        report += "⚠️ الحسابات التي فشلت:\n"
        for account in failed_accounts:
            report += f"- {account}\n"
        report += "\nيرجى التحقق من صلاحية هذه الحسابات."

    await status_message.edit_text(
        report,
        reply_markup=create_keyboard(
            [
                [(ArabicText.BACK, "services:menu")],
                [(ArabicText.HOME_TITLE, "home")],
            ]
        ),
    )

    # try:
    #     if screenshots:
    #         chunks = [screenshots[i : i + 10] for i in range(0, len(screenshots), 10)]
    #         for chunk in chunks:
    #             await status_message.reply_media_group(chunk)
    # except TimeoutError:
    #     ...
