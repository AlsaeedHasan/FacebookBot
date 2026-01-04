import json
import os
from typing import Any, Dict, List, Optional, Union


class Database:
    """Simple JSON database for the bot"""

    def __init__(self, db_path: str, superuser: Dict):
        """Initialize the database

        Args:
            db_path (str): Path to the database file
        """
        self.db_path = db_path
        self.data = self._load_db(superuser)

    def _load_db(self, superuser: Dict) -> Dict:
        """Load the database from the file

        Returns:
            Dict: Database data
        """
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        # Create file if it doesn't exist
        if not os.path.exists(self.db_path):
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "superuser": {
                            "username": superuser["username"],
                            "password": superuser["password"],
                            "sessions": [],
                        },
                        "bot_users": {},
                        "sessions": {},
                        "facebook_accounts": {},
                    },
                    f,
                    ensure_ascii=False,
                    indent=4,
                )

        # Load the database
        with open(self.db_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_db(self) -> None:
        """Save the database to the file"""
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)

    def is_authenticated(self, telegram_id: int) -> bool:
        """Check if a user is authenticated

        Args:
            telegram_id (int): Telegram user ID

        Returns:
            bool: True if authenticated, False otherwise
        """
        return str(telegram_id) in self.data["sessions"]

    def get_authenticated_username(self, telegram_id: int) -> Optional[str]:
        """Get the username of an authenticated user

        Args:
            telegram_id (int): Telegram user ID

        Returns:
            Optional[str]: Username if authenticated, None otherwise
        """
        if not self.is_authenticated(telegram_id):
            return None

        return self.data["sessions"][str(telegram_id)]

    def authenticate_user(self, username: str, password: str) -> bool:
        """Authenticate a user with username and password

        Args:
            username (str): Username
            password (str): Password

        Returns:
            bool: True if authentication successful, False otherwise
        """
        # Check superuser
        if (
            username == self.data["superuser"]["username"]
            and password == self.data["superuser"]["password"]
        ):
            return True

        # Check bot users
        if (
            username in self.data["bot_users"]
            and self.data["bot_users"][username]["password"] == password
        ):
            return True

        return False

    def create_session(self, telegram_id: int, username: str) -> None:
        """Create a session for a user

        Args:
            telegram_id (int): Telegram user ID
            username (str): Username
        """
        # Add session to sessions
        self.data["sessions"][str(telegram_id)] = username

        # Add telegram_id to user sessions
        if username == self.data["superuser"]["username"]:
            if "sessions" not in self.data["superuser"]:
                self.data["superuser"]["sessions"] = []
            self.data["superuser"]["sessions"].append(str(telegram_id))
        elif username in self.data["bot_users"]:
            if "sessions" not in self.data["bot_users"][username]:
                self.data["bot_users"][username]["sessions"] = []
            self.data["bot_users"][username]["sessions"].append(str(telegram_id))

        self._save_db()

    def end_session(self, telegram_id: int) -> None:
        """End a user session

        Args:
            telegram_id (int): Telegram user ID
        """
        if not self.is_authenticated(telegram_id):
            return

        username = self.data["sessions"][str(telegram_id)]

        # Remove session from sessions
        if str(telegram_id) in self.data["sessions"]:
            del self.data["sessions"][str(telegram_id)]

        # Remove telegram_id from user sessions
        if username == self.data["superuser"]["username"]:
            if (
                "sessions" in self.data["superuser"]
                and str(telegram_id) in self.data["superuser"]["sessions"]
            ):
                self.data["superuser"]["sessions"].remove(str(telegram_id))
        elif username in self.data["bot_users"]:
            if (
                "sessions" in self.data["bot_users"][username]
                and str(telegram_id) in self.data["bot_users"][username]["sessions"]
            ):
                self.data["bot_users"][username]["sessions"].remove(str(telegram_id))

        self._save_db()

    def get_session(self, telegram_id: int) -> Optional[str]:
        """Get the username of an authenticated user

        Args:
            telegram_id (int): Telegram user ID

        Returns:
            Optional[str]: Username if authenticated, None otherwise
        """
        if not self.is_authenticated(telegram_id):
            return None

        return self.data["sessions"][str(telegram_id)]

    def is_superuser(self, telegram_id: int) -> bool:
        """Check if a user is a superuser

        Args:
            telegram_id (int): Telegram user ID

        Returns:
            bool: True if superuser, False otherwise
        """
        if not self.is_authenticated(telegram_id):
            return False

        username = self.get_authenticated_username(telegram_id)
        return username == self.data["superuser"]["username"]

    def get_all_bot_users(self) -> Dict:
        """Get all bot users

        Returns:
            Dict: All bot users
        """
        return self.data["bot_users"]

    def get_bot_user(self, username: str) -> Optional[Dict]:
        """Get a bot user

        Args:
            username (str): Username

        Returns:
            Optional[Dict]: User data if exists, None otherwise
        """
        return self.data["bot_users"].get(username)

    def add_bot_user(
        self, username: str, password: str, is_admin: bool = False
    ) -> bool:
        """Add a bot user

        Args:
            username (str): Username
            password (str): Password
            is_admin (bool, optional): Whether the user is an admin. Defaults to False.

        Returns:
            bool: True if successful, False otherwise
        """
        # Check if username already exists
        if (
            username in self.data["bot_users"]
            or username == self.data["superuser"]["username"]
        ):
            return False

        # Add user
        self.data["bot_users"][username] = {
            "username": username,
            "password": password,
            "is_admin": is_admin,
            "sessions": [],
            "facebook_accounts": [],
        }
        self._save_db()
        return True

    def remove_bot_user(self, username: str) -> None:
        """Remove a bot user

        Args:
            username (str): Username
        """
        if username not in self.data["bot_users"]:
            return

        # Remove all sessions for this user
        for telegram_id in self.data["bot_users"][username].get("sessions", []):
            if telegram_id in self.data["sessions"]:
                del self.data["sessions"][telegram_id]

        # Remove user
        del self.data["bot_users"][username]
        self._save_db()

    def add_facebook_account(
        self,
        email: str,
        password: Optional[str] = None,
        cookies_path: Optional[str] = None,
        proxy: Optional[str] = None,
    ) -> None:
        """Add a Facebook account to the database

        Args:
            email (str): Facebook email
            password (Optional[str], optional): Facebook password. Defaults to None.
            cookies_path (Optional[str], optional): Path to cookies file. Defaults to None.
            proxy (Optional[str], optional): Proxy string for this account. Defaults to None.
        """
        # If account exists, update it while preserving existing proxy if not provided
        existing_account = self.data["facebook_accounts"].get(email, {})

        self.data["facebook_accounts"][email] = {
            "email": email,
            "password": password if password else existing_account.get("password"),
            "cookies_path": (
                cookies_path if cookies_path else existing_account.get("cookies_path")
            ),
            "proxy": proxy if proxy else existing_account.get("proxy"),
        }
        self._save_db()

    def get_facebook_account(self, email: str) -> Optional[Dict]:
        """Get a Facebook account from the database

        Args:
            email (str): Facebook email

        Returns:
            Optional[Dict]: Account data if exists, None otherwise
        """
        return self.data["facebook_accounts"].get(email)

    def update_facebook_account(self, email: str, data: Dict) -> None:
        """Update a Facebook account in the database

        Args:
            email (str): Facebook email
            data (Dict): New account data
        """
        if email in self.data["facebook_accounts"]:
            self.data["facebook_accounts"][email].update(data)
            self._save_db()

    def add_facebook_account_to_user(self, username: str, email: str) -> None:
        """Add a Facebook account to a user

        Args:
            username (str): Username
            email (str): Facebook email
        """
        # Check if account exists
        if email not in self.data["facebook_accounts"]:
            return

        # Add to superuser
        if username == self.data["superuser"]["username"]:
            if "facebook_accounts" not in self.data["superuser"]:
                self.data["superuser"]["facebook_accounts"] = []
            if email not in self.data["superuser"]["facebook_accounts"]:
                self.data["superuser"]["facebook_accounts"].append(email)
        # Add to bot user
        elif username in self.data["bot_users"]:
            if "facebook_accounts" not in self.data["bot_users"][username]:
                self.data["bot_users"][username]["facebook_accounts"] = []
            if email not in self.data["bot_users"][username]["facebook_accounts"]:
                self.data["bot_users"][username]["facebook_accounts"].append(email)

        self._save_db()

    def get_bot_user_facebook_accounts(self, username: str) -> List[str]:
        """Get Facebook accounts for a user

        Args:
            username (str): Username

        Returns:
            List[str]: List of Facebook emails
        """
        # Check superuser
        if username == self.data["superuser"]["username"]:
            return self.data["superuser"].get("facebook_accounts", [])

        # Check bot users
        if username in self.data["bot_users"]:
            return self.data["bot_users"][username].get("facebook_accounts", [])

        return []

    def is_facebook_account_owner(self, username: str, email: str) -> bool:
        """Check if a user owns a Facebook account

        Args:
            username (str): Username
            email (str): Facebook email

        Returns:
            bool: True if owner, False otherwise
        """
        accounts = self.get_bot_user_facebook_accounts(username)
        return email in accounts

    def remove_facebook_account(self, email: str) -> None:
        """Remove a Facebook account from the database

        Args:
            email (str): Facebook email
        """
        if email not in self.data["facebook_accounts"]:
            return

        # Remove from superuser
        if "facebook_accounts" in self.data["superuser"]:
            if email in self.data["superuser"]["facebook_accounts"]:
                self.data["superuser"]["facebook_accounts"].remove(email)

        # Remove from all bot users
        for username, user_data in self.data["bot_users"].items():
            if "facebook_accounts" in user_data:
                if email in user_data["facebook_accounts"]:
                    user_data["facebook_accounts"].remove(email)

        # Remove account
        del self.data["facebook_accounts"][email]
        self._save_db()

    def remove_facebook_account_from_user(self, username: str, email: str) -> None:
        """Remove a Facebook account from a user

        Args:
            username (str): Username
            email (str): Facebook email
        """
        # Remove from superuser
        if username == self.data["superuser"]["username"]:
            if "facebook_accounts" in self.data["superuser"]:
                if email in self.data["superuser"]["facebook_accounts"]:
                    self.data["superuser"]["facebook_accounts"].remove(email)
                    self._save_db()

        # Remove from bot user
        elif username in self.data["bot_users"]:
            if "facebook_accounts" in self.data["bot_users"][username]:
                if email in self.data["bot_users"][username]["facebook_accounts"]:
                    self.data["bot_users"][username]["facebook_accounts"].remove(email)
                    self._save_db()
