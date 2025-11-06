from functools import wraps

from flask import abort
from flask_login import current_user

from app.models import UserRole


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != UserRole.ADMIN:
            abort(403)
        return f(*args, **kwargs)

    return decorated_function


def librarian_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in (UserRole.ADMIN, UserRole.LIBRARIAN):
            abort(403)
        return f(*args, **kwargs)

    return decorated_function


def role_required(role: UserRole):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or not current_user.has_role(role):
                abort(403)
            return f(*args, **kwargs)

        return decorated_function

    return decorator
