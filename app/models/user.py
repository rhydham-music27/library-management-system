from datetime import datetime
from enum import Enum

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db


class UserRole(Enum):
    ADMIN = "admin"
    LIBRARIAN = "librarian"
    MEMBER = "member"


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.MEMBER)
    _is_active = db.Column('is_active', db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password, method="pbkdf2:sha256")

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def has_role(self, role: "UserRole") -> bool:
        if self.role == UserRole.ADMIN:
            return True
        if role == UserRole.MEMBER and self.role in {UserRole.LIBRARIAN, UserRole.MEMBER}:
            return True
        if role == UserRole.LIBRARIAN and self.role == UserRole.LIBRARIAN:
            return True
        return self.role == role

    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN

    def is_librarian(self) -> bool:
        return self.role in {UserRole.ADMIN, UserRole.LIBRARIAN}

    def is_member(self) -> bool:
        return self.role in {UserRole.ADMIN, UserRole.LIBRARIAN, UserRole.MEMBER}

    # Override property from UserMixin to reflect column value
    @property
    def is_active(self) -> bool:  # type: ignore[override]
        return bool(self._is_active)

    def __repr__(self) -> str:
        return f"<User {self.username}>"
