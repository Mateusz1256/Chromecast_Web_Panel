import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash


@dataclass
class User(UserMixin):
    id: str
    username: str
    password_hash: str


class UserStore:
    def __init__(self, database_path: str):
        self.database_path = database_path

    def init_db(self) -> None:
        Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL
                )
                """
            )

    def create_admin(self, username: str, password: str) -> User:
        if not username:
            raise ValueError("Username is required")
        if not password:
            raise ValueError("Password is required")

        self.init_db()
        password_hash = generate_password_hash(password)
        with self._connect() as connection:
            cursor = connection.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, password_hash),
            )
            user_id = str(cursor.lastrowid)
        return User(id=user_id, username=username, password_hash=password_hash)

    def get_by_id(self, user_id: str) -> Optional[User]:
        self.init_db()
        with self._connect() as connection:
            row = connection.execute(
                "SELECT id, username, password_hash FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
        return _row_to_user(row)

    def get_by_username(self, username: str) -> Optional[User]:
        self.init_db()
        with self._connect() as connection:
            row = connection.execute(
                "SELECT id, username, password_hash FROM users WHERE username = ?",
                (username,),
            ).fetchone()
        return _row_to_user(row)

    def authenticate(self, username: str, password: str) -> Optional[User]:
        user = self.get_by_username(username)
        if user is None:
            return None
        if not check_password_hash(user.password_hash, password):
            return None
        return user

    def has_users(self) -> bool:
        self.init_db()
        with self._connect() as connection:
            row = connection.execute("SELECT COUNT(*) AS count FROM users").fetchone()
        return bool(row["count"])

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection


def _row_to_user(row: Optional[sqlite3.Row]) -> Optional[User]:
    if row is None:
        return None
    return User(
        id=str(row["id"]),
        username=row["username"],
        password_hash=row["password_hash"],
    )
