from flask_login import UserMixin
from db.core import query_one

class User(UserMixin):
    def __init__(self, id, username, email, electricity_rate):
        self.id = id
        self.username = username
        self.email = email
        self.electricity_rate = electricity_rate

    @staticmethod
    def from_row(row):
        if not row:
            return None
        return User(
            id=row["id"],
            username=row["username"],
            email=row["email"],
            electricity_rate=row["electricity_rate"],
        )

def get_user_by_id(user_id: int):
    row = query_one("SELECT * FROM users WHERE id = ?", (user_id,))
    return User.from_row(row)

def get_user_by_email(email: str):
    row = query_one("SELECT * FROM users WHERE email = ?", (email,))
    return User.from_row(row)

def get_user_by_username(username: str):
    row = query_one("SELECT * FROM users WHERE username = ?", (username,))
    return User.from_row(row)
