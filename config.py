import os
from pathlib import Path
from datetime import timedelta

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")

    # CSRF / WTForms
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    WTF_CSRF_SSL_STRICT = False

    # Session / cookies
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = timedelta(days=30)

    # Circulation settings
    LOAN_PERIOD_DAYS = int(os.getenv("LOAN_PERIOD_DAYS", 14))
    MAX_ACTIVE_LOANS = int(os.getenv("MAX_ACTIVE_LOANS", 5))
    # Fine rate per day for overdue books (in dollars)
    FINE_RATE_PER_DAY = float(os.getenv('FINE_RATE_PER_DAY', '1.0'))

    # Database
    # Build an absolute path to the instance database by default to avoid
    # sqlite3 "unable to open database file" when CWD is different.
    _BASEDIR = Path(__file__).resolve().parent
    # Use the Flask package instance folder (app/instance) to match app.instance_path
    _INSTANCE_DIR = (_BASEDIR / "app" / "instance")
    _DEFAULT_DB_PATH = _INSTANCE_DIR / "library.db"
    # Use forward slashes for SQLAlchemy URI on Windows
    _DEFAULT_DB = f"sqlite:///{_DEFAULT_DB_PATH.as_posix()}"
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", _DEFAULT_DB)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # SQLAlchemy engine options
    SQLALCHEMY_ENGINE_OPTIONS = {
        # For SQLite in multi-threaded environments
        "connect_args": {"check_same_thread": False} if SQLALCHEMY_DATABASE_URI.startswith("sqlite") else {},
        # Connection pool health
        "pool_pre_ping": True,
        # Recycle connections hourly
        "pool_recycle": 3600,
        # Echo can be toggled per environment
        "echo": False,
    }


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_ECHO = False
    # Add production-specific settings here (e.g., secure cookies, logging)
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    WTF_CSRF_SSL_STRICT = True


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ECHO = False


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
