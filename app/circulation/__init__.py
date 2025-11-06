from flask import Blueprint

bp = Blueprint('circulation', __name__, url_prefix='/circulation')

# Import routes at the end to avoid circular imports
from . import routes  # noqa: E402,F401
