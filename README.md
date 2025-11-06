# Library Management System (Flask)

A modular Flask application foundation for a full-featured Library Management System. This phase sets up the architecture, configuration, database plumbing, UI base with Bootstrap 5, and helpful CLI commands.

## Technologies Used

- Python 3.x
- Flask web framework
- SQLite database with WAL mode and foreign key enforcement
- SQLAlchemy ORM via Flask-SQLAlchemy
- Flask-Migrate (Alembic) for migrations
- Bootstrap 5 for UI
- Flask-Login for session management
- Flask-WTF (WTForms) for forms and CSRF protection

## Project Structure

```
.
├── app/
│   ├── __init__.py            # Application factory, CLI, error handlers
│   ├── extensions.py          # db, migrate instances
│   ├── main/                  # Main blueprint
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── models/                # ORM models
│   │   ├── __init__.py
│   │   ├── book.py
│   │   └── category.py
│   ├── catalog/               # Catalog blueprint (books & categories)
│   │   ├── __init__.py
│   │   ├── forms.py
│   │   └── routes.py
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css
│   │   ├── js/
│   │   │   └── main.js
│   │   └── images/
│   │       └── .gitkeep
│   └── templates/
│       ├── base.html
│       ├── errors/
│       │   ├── 404.html
│       │   └── 500.html
│       ├── catalog/
│       │   ├── book_detail.html
│       │   ├── book_form.html
│       │   ├── books.html
│       │   ├── categories.html
│       │   └── category_form.html
│       └── main/
│           ├── about.html
│           └── index.html
├── instance/
│   └── .gitkeep               # Folder for sqlite DB and local overrides
├── config.py                  # Environment-based configuration
├── requirements.txt           # Python dependencies
├── .env.example               # Example environment configuration
├── .flaskenv                  # Flask CLI defaults for dev
├── .gitignore                 # Ignore rules
├── run.py                     # Dev entry point and Flask CLI target
└── README.md
```

## Installation

- Ensure Python 3.10+ is installed.
- Create and activate a virtual environment.
- Install dependencies:

```bash
pip install -r requirements.txt
```

- Create your environment file:

```bash
copy .env.example .env   # Windows (PowerShell: cp .env.example .env)
```

- Adjust values in `.env` as needed. The default SQLite DB lives at `instance/library.db`.

## Database Setup

You can use either direct table creation (foundation) or migrations (recommended for future phases).

- Initialize database (creates all tables defined by models):

```bash
flask init-db
```

- Set up migrations and upgrade (once models are added):

```bash
flask db init
flask db migrate -m "initial"
flask db upgrade
```

- Seed sample data and default users:

```bash
flask seed-db
```

- Reset database (DANGEROUS):

```bash
flask reset-db
```

## Authentication System

Role-based access control with three roles: Admin, Librarian, Member.

Default credentials created by `flask seed-db` (change these in production):

- Admin: username `admin`, password `admin123`
- Librarian: username `librarian`, password `librarian123`
- Member: username `member`, password `member123`

### User Roles and Permissions

- Admin: Full system access, user management
- Librarian: Book and member management, circulation
- Member: View catalog, borrow books, view own history

Note: Detailed permissions will be enforced progressively in subsequent phases.

## Running the Application

- Using Flask CLI:

```bash
flask run
```

- Or directly:

```bash
python run.py
```

Open http://localhost:5000 in your browser.

## Configuration

- `.env` variables:
  - `FLASK_APP` (default: run.py)
  - `FLASK_ENV` (development|production|testing)
  - `FLASK_DEBUG` (1|0)
  - `SECRET_KEY`
  - `DATABASE_URL` (e.g., `sqlite:///instance/library.db`)

### Security Best Practices

- Change default passwords immediately after seeding
- Use a strong `SECRET_KEY` in production
- Enable HTTPS and secure cookies in production
- Keep dependencies up to date

- Development vs Production:
  - Development: Debug on, SQL echo enabled.
  - Production: Debug off, SQL echo off, add hardened settings as needed.

## Future Enhancements

- Authentication and user roles
- Members management
- Circulation (issue/return), fines
- Reporting and dashboards

## Book Catalog Management

Comprehensive catalog with books and categories.

- Fields captured per book: ISBN, title, author, publisher, publication year, edition, language, pages, description, category, quantity, shelf location
- Categories organize books (one-to-many)
- Search and filters: title/author/ISBN text search, by category, and by availability
- Pagination: 20 books per page
- Role-based access:
  - All authenticated users can browse and view details
  - Librarians/Admins can add/edit/delete books and categories

### Usage

- Browse books: Navbar → Books
- Search: use the filters at the top of the list; Clear resets filters
- Add a book: Books → Add New Book (librarian/admin)
- Manage categories: Use Categories page in Catalog (librarian/admin)

### CLI Seed Data

`flask seed-db` creates:

- Categories: Fiction, Non-Fiction, Science, Technology, History, Children
- Sample books across categories (e.g., Clean Code, Sapiens, To Kill a Mockingbird, etc.)

## Member Management

Comprehensive management for library members with auto-generated IDs and status tracking.

- Fields per member: member_id (auto-generated), name, email, phone, address, registration_date, status, notes
- Unique member ID format: `MEM-{YEAR}-{6-digit-random}` (e.g., `MEM-2024-123456`)
- Status types:
  - Active: Can borrow books, in good standing
  - Suspended: Temporarily suspended (e.g., overdue books, unpaid fines)
  - Expired: Membership expired, needs renewal
- Search and filters: by name, email, member_id, and status
- Pagination: 20 members per page
- Role-based access: only Librarians/Admins can manage members
- Operations: register, view, edit, delete, and quick status change

### Usage

- Browse members: Navbar → Members (visible to librarian/admin)
- Register new member: Dashboard button or Members → Register New Member
- Search/filter: use the filters on the Members page; Clear resets filters
- Change status: buttons on the Member Detail page (Activate, Suspend, Expire)

### CLI Seed Data (updated)

`flask seed-db` now also creates sample members with varied statuses. Member IDs are auto-generated.

### Project Structure (updated)

```
app/
  members/
    __init__.py
    forms.py
    routes.py
  models/
    member.py
templates/
  members/
    members.html
    member_detail.html
    member_form.html
```

### Features (updated)

- Member Management:

## Circulation System

End-to-end book borrowing and returns with validation and tracking.

- Loan tracking with status (borrowed, returned)
- Fields: book, member, borrow_date, due_date, return_date, status, notes
- Business rules:
  - Default loan period: 14 days (configurable via `LOAN_PERIOD_DAYS`)
  - Maximum active loans per member: 5 (configurable via `MAX_ACTIVE_LOANS`)
  - Members must be active to borrow; members with overdue books cannot borrow
  - Books must be available (quantity > active loans); duplicate active loans prevented
- Operations:
  - Issue Book: choose member/book, optional custom due date
  - Return Book: select active loan, optional return date
  - Overdue detection: automatic when due_date < today for active loans
- Views:
  - Loans listing with filters (query, status, member) and pagination (20/page)
  - Loan detail page with status/overdue info and metadata
  - Member borrowing history
  - Book loan history

### Usage

- Navbar → Circulation → Loans | Issue Book | Return Book
- From Book Detail: View Loan History (librarian/admin) and Borrow button (for members when available)
- From Member Detail: View Borrowing History

### Configuration (updated)

Add environment variables or override in config:

- `LOAN_PERIOD_DAYS` (default 14)
- `MAX_ACTIVE_LOANS` (default 5)

### Database Schema (updated)

- New `loans` table; relationships Loan→Book, Loan→Member
- Book `available_quantity` computed as quantity minus active loans

### CLI Seed Data (updated)

`flask seed-db` now creates sample loans with a variety of active/returned/overdue cases.

### Project Structure (additions)

```
app/
  circulation/
    __init__.py
    forms.py
    routes.py
  models/
    loan.py
templates/
  circulation/
    loans.html
    loan_detail.html
    borrow_form.html
    return_form.html
    member_history.html
    book_history.html
```

## Reports & Analytics

Comprehensive reporting for librarians and admins with interactive charts and exports.

- Dashboard with overview statistics and charts
- Report types:
  - Most Borrowed Books: ranking with date range filters
  - Active Members: top borrowers and member activity
  - Overdue Summary: current overdue breakdown and details
  - Collection Statistics: books by category and availability
  - Circulation Trends: time-series of loans over time
- Features:
  - Interactive charts using Chart.js 4.4.1 (via CDN)
  - Date range filtering using Flask-WTF
  - CSV export for spreadsheets
  - PDF export using WeasyPrint 62.3
  - Role-based access (librarian/admin)

### Usage

- Navbar → Reports → choose any report (visible to librarian/admin)
- Adjust Start/End date and Apply Filter
- Use Export buttons to download CSV/PDF

### Technologies (additional)

- Chart.js 4.4.1 for data visualization (CDN)
- WeasyPrint 62.3 for HTML-to-PDF export
- Python csv (built-in) for CSV export

### Project Structure (additions)

```
app/
  reports/
    __init__.py
    forms.py
    utils.py
    routes.py
templates/
  reports/
    dashboard.html
    most_borrowed.html
    active_members.html
    overdue_summary.html
    collection_stats.html
    circulation_trends.html
    most_borrowed_pdf.html
```

### Notes

- Some reports perform aggregations; limit date ranges for best performance on large datasets.
- Seed data created by `flask seed-db` is sufficient to test reports.

## License and Contributing

- Apache 2.0
- Contributions welcome via pull requests
