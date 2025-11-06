from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

# Centralized extension instances to avoid circular imports

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
