from flask import Blueprint

bp = Blueprint('catalog', __name__, url_prefix='/catalog')

# Import routes at the end to avoid circular imports
from . import routes  # noqa: E402,F401
