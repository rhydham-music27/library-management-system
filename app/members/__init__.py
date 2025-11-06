from flask import Blueprint

bp = Blueprint('members', __name__, url_prefix='/members')

from . import routes  # noqa: E402,F401
