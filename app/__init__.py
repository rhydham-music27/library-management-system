import os
import click
from flask import Flask, render_template
from flask_wtf.csrf import generate_csrf
from .extensions import db, migrate, login_manager, csrf
from .main import bp as main_bp
from .auth import bp as auth_bp
from .catalog import bp as catalog_bp
from .members import bp as members_bp
from .circulation import bp as circulation_bp
from .reports import bp as reports_bp
from urllib.parse import urlparse, unquote
import re


def create_app(config_name: str = "development") -> Flask:
    """Application factory for the Library Management System."""
    app = Flask(__name__, instance_relative_config=True)

    # Load configuration
    from config import config as config_map

    cfg_class = config_map.get(config_name, config_map["development"])()
    app.config.from_object(cfg_class)

    # Ensure SQLite directory exists for the configured database URI
    try:
        uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        if uri.startswith("sqlite") and ":memory:" not in uri:
            parsed = urlparse(uri)
            path = unquote(parsed.path or "")
            # On Windows, urlparse gives paths like '/C:/...'
            if os.name == 'nt' and path.startswith('/') and re.match(r'^/[A-Za-z]:', path):
                path = path[1:]
            db_dir = os.path.dirname(path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
    except Exception:
        pass

    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    # Enable CSRF protection
    csrf.init_app(app)

    # Flask-Login user loader
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        try:
            return User.query.get(int(user_id))
        except Exception:
            return None

    # SQLite PRAGMA configuration via SQLAlchemy event hooks
    _configure_sqlite_pragmas(app)

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(catalog_bp)
    app.register_blueprint(members_bp)
    app.register_blueprint(circulation_bp)
    app.register_blueprint(reports_bp)

    # Error handlers
    register_error_handlers(app)

    # Template context processors
    @app.context_processor
    def inject_globals():
        return {
            "app_name": "Library Management System",
            "csrf_token": generate_csrf,
        }

    # CLI commands
    register_cli_commands(app)

    return app


def _configure_sqlite_pragmas(app: Flask) -> None:
    """Configure SQLite-specific PRAGMAs for performance and integrity."""
    from sqlalchemy import event
    from sqlalchemy.engine import Engine
    import sqlite3

    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        # Only apply to SQLite connections
        if isinstance(dbapi_connection, sqlite3.Connection):  # pragma: no cover
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA foreign_keys=ON;")
            cursor.execute("PRAGMA synchronous=NORMAL;")
            cursor.close()


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(404)
    def not_found(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(error):
        return render_template("errors/500.html"), 500

    @app.errorhandler(403)
    def forbidden(error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(400)
    def bad_request(error):
        return render_template("errors/400.html"), 400

    @app.errorhandler(401)
    def unauthorized(error):
        return render_template("errors/401.html"), 401

    @app.errorhandler(429)
    def too_many_requests(error):
        return render_template("errors/429.html"), 429

    # Generic exception handler in production only
    if not app.config.get('DEBUG', False):
        from werkzeug.exceptions import HTTPException

        @app.errorhandler(Exception)
        def handle_exception(error):
            try:
                if isinstance(error, HTTPException):
                    code = getattr(error, 'code', 500) or 500
                    if code == 400:
                        return render_template("errors/400.html"), 400
                    if code == 401:
                        return render_template("errors/401.html"), 401
                    if code == 403:
                        return render_template("errors/403.html"), 403
                    if code == 404:
                        return render_template("errors/404.html"), 404
                    if code == 429:
                        return render_template("errors/429.html"), 429
                    return render_template("errors/500.html"), code
                # Log and return 500 for non-HTTP exceptions
                app.logger.error("Unhandled exception: %s", error, exc_info=True)
                return render_template("errors/500.html"), 500
            except Exception:
                return render_template("errors/500.html"), 500


def register_cli_commands(app: Flask) -> None:
    @app.cli.command("init-db")
    def init_db():
        """Initialize the database (create all tables)."""
        with app.app_context():
            db.create_all()
        click.echo("Database initialized.")

    @app.cli.command("seed-db")
    def seed_db():
        """Seed the database with initial sample data and default users."""
        from app.models import User, UserRole, Category, Book, Member, MemberStatus, Loan, LoanStatus
        with app.app_context():
            db.create_all()
            created = []
            # Admin
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                admin = User(username='admin', email='admin@library.com', full_name='System Administrator', role=UserRole.ADMIN)
                admin.set_password('admin123')  # WARNING: Change in production
                db.session.add(admin)
                created.append('admin')
            # Librarian
            librarian = User.query.filter_by(username='librarian').first()
            if not librarian:
                librarian = User(username='librarian', email='librarian@library.com', full_name='Librarian', role=UserRole.LIBRARIAN)
                librarian.set_password('librarian123')
                db.session.add(librarian)
                created.append('librarian')
            # Member
            member = User.query.filter_by(username='member').first()
            if not member:
                member = User(username='member', email='member@library.com', full_name='Member', role=UserRole.MEMBER)
                member.set_password('member123')
                db.session.add(member)
                created.append('member')
            db.session.commit()

            # Seed Categories
            if Category.query.count() == 0:
                categories = [
                    Category(name='Fiction', description='Novels, short stories, and other fictional works'),
                    Category(name='Non-Fiction', description='Biographies, essays, and factual books'),
                    Category(name='Science', description='Scientific texts, research, and discoveries'),
                    Category(name='Technology', description='Computer science, engineering, and technical books'),
                    Category(name='History', description='Historical accounts and documentaries'),
                    Category(name='Children', description='Books for young readers'),
                ]
                db.session.add_all(categories)
                db.session.commit()
                click.echo(f"Created {len(categories)} categories")

            # Seed Books
            if Book.query.count() == 0:
                def cat(name):
                    return Category.query.filter_by(name=name).first()

                books = [
                    Book(title='To Kill a Mockingbird', author='Harper Lee', publisher='J.B. Lippincott & Co.', publication_year=1960, edition='1st', language='English', pages=281, description='A novel about racial injustice in the Deep South.', category_id=cat('Fiction').id if cat('Fiction') else None, quantity=3, isbn='9780061120084'),
                    Book(title='A Brief History of Time', author='Stephen Hawking', publisher='Bantam Books', publication_year=1988, language='English', pages=212, description='Cosmology for the masses.', category_id=cat('Science').id if cat('Science') else None, quantity=2, isbn='9780553380163'),
                    Book(title='Clean Code', author='Robert C. Martin', publisher='Prentice Hall', publication_year=2008, language='English', pages=464, description='A Handbook of Agile Software Craftsmanship.', category_id=cat('Technology').id if cat('Technology') else None, quantity=5, isbn='9780132350884'),
                    Book(title='Sapiens', author='Yuval Noah Harari', publisher='Harper', publication_year=2011, language='English', pages=498, description='A brief history of humankind.', category_id=cat('History').id if cat('History') else None, quantity=4, isbn='9780062316097'),
                    Book(title='The Cat in the Hat', author='Dr. Seuss', publisher='Random House', publication_year=1957, language='English', pages=61, description='Classic children book.', category_id=cat('Children').id if cat('Children') else None, quantity=2),
                    Book(title='The Pragmatic Programmer', author='Andrew Hunt, David Thomas', publisher='Addison-Wesley', publication_year=1999, language='English', pages=352, description='Journey to Mastery.', category_id=cat('Technology').id if cat('Technology') else None, quantity=3, isbn='9780201616224'),
                ]
                db.session.add_all(books)
                db.session.commit()
                click.echo(f"Created {len(books)} books")
            # Seed Members
            if Member.query.count() == 0:
                from datetime import timedelta, date as _date
                import random as _rand

                def _mk(name, email, phone=None, address=None, status=MemberStatus.ACTIVE, notes=None):
                    return Member(
                        member_id=Member.generate_member_id(),
                        name=name,
                        email=email,
                        phone=phone,
                        address=address,
                        registration_date=_date.today() - timedelta(days=_rand.randint(30, 365)),
                        status=status,
                        notes=notes,
                    )

                members = [
                    _mk('John Smith', 'john.smith@email.com', '+1-555-0101', '123 Main St, City, State', MemberStatus.ACTIVE),
                    _mk('Sarah Johnson', 'sarah.j@email.com', '+1-555-0102', '456 Oak Ave, City, State', MemberStatus.ACTIVE),
                    _mk('Michael Brown', 'michael.b@email.com', '+1-555-0103', status=MemberStatus.SUSPENDED, notes='Suspended due to overdue books'),
                    _mk('Emily Davis', 'emily.davis@email.com', '+1-555-0104', status=MemberStatus.ACTIVE),
                    _mk('Robert Wilson', 'robert.w@email.com', status=MemberStatus.EXPIRED, notes='Membership expired, needs renewal'),
                    _mk('Lisa Anderson', 'lisa.a@email.com', '+1-555-0105', status=MemberStatus.ACTIVE),
                ]
                db.session.add_all(members)
                db.session.commit()
                click.echo(f"Created {len(members)} members")
            
            # Seed Loans
            if Loan.query.count() == 0:
                from datetime import timedelta, date as _date
                import random as _rand
                from decimal import Decimal as _Dec
                members_all = Member.query.all()
                books_all = Book.query.all()
                sample = []
                if members_all and books_all:
                    for i in range(10):
                        m = _rand.choice(members_all)
                        b = _rand.choice(books_all)
                        days_ago = _rand.randint(1, 60)
                        borrow_dt = _date.today() - timedelta(days=days_ago)
                        due_dt = borrow_dt + timedelta(days=14)
                        returned = _rand.choice([True, False, False])  # more active than returned
                        loan = Loan(
                            book_id=b.id,
                            member_id=m.id,
                            borrow_date=borrow_dt,
                            due_date=due_dt,
                            status=LoanStatus.BORROWED,
                            notes=_rand.choice([None, 'Handle with care', 'Slightly worn cover'])
                        )
                        if returned:
                            # return sometime between borrow and today
                            ret_offset = _rand.randint(max(1, days_ago - 10), max(1, days_ago))
                            loan.return_date = borrow_dt + timedelta(days=ret_offset)
                            loan.status = LoanStatus.RETURNED
                        sample.append(loan)
                    db.session.add_all(sample)
                    db.session.commit()
                    # Compute fines for overdue active loans and set varied fine states for returned loans
                    updated = 0
                    for loan in sample:
                        try:
                            # For active overdue loans, calculate current fine
                            if loan.status == LoanStatus.BORROWED and loan.due_date < _date.today():
                                loan.update_fine_amount()
                                updated += 1
                            # For returned loans, create variety of paid statuses
                            if loan.status == LoanStatus.RETURNED:
                                # Determine overdue days relative to return date
                                overdue_days = max(0, (loan.return_date - loan.due_date).days) if loan.return_date and loan.return_date > loan.due_date else 0
                                if overdue_days > 0:
                                    # Fine amount per configured rate (fallback 1.0)
                                    rate = float(app.config.get('FINE_RATE_PER_DAY', 1.0))
                                    total = _Dec(str(overdue_days)) * _Dec(str(rate))
                                    loan.fine_amount = total
                                    # Randomize paid state: fully paid, partial, or unpaid
                                    state = _rand.choice(['full', 'partial', 'unpaid'])
                                    if state == 'full':
                                        loan.fine_paid = total
                                    elif state == 'partial':
                                        # pay between 25% and 75%
                                        pct = _Dec(str(_rand.randint(25, 75))) / _Dec('100')
                                        loan.fine_paid = (total * pct).quantize(_Dec('0.01'))
                                    else:
                                        loan.fine_paid = _Dec('0.00')
                                    updated += 1
                        except Exception:
                            pass
                    db.session.commit()
                    click.echo(f"Created {len(sample)} loans with varied fine statuses for testing (updated {updated})")
        if created:
            click.echo("Created default users: " + ", ".join(created))
        click.echo("Seed complete. Default credentials (change in production):\n"
                   "  admin / admin123\n  librarian / librarian123\n  member / member123")

    @app.cli.command("reset-db")
    def reset_db():
        """Drop and recreate the database (DANGEROUS)."""
        if click.confirm("This will DROP all tables and recreate them. Continue?", default=False):
            with app.app_context():
                db.drop_all()
                db.create_all()
            click.echo("Database reset completed.")
        else:
            click.echo("Aborted.")
