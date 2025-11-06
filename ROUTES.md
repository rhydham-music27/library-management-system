# User Guide: Application Routes & Default Accounts

This document lists the main routes available in the Library Management System, their functionality, and access requirements. It also includes default user accounts for testing.

## Default Users (for local development)

- Admin: username `admin`, password `admin123`
- Librarian: username `librarian`, password `librarian123`
- Member: username `member`, password `member123`

Notes:
- These are created by running `flask seed-db`.
- Change these in production.

## Legend

- Method: GET, POST
- Auth: whether login is required
- Role: extra restriction
- Path prefixes by blueprint:
  - Main: `/`
  - Auth: `/auth`
  - Catalog: `/catalog`
  - Members: `/members`
  - Circulation: `/circulation`
  - Reports: `/reports`

---

## Main

- GET `/` or `/index`
  - Auth: not required
  - Role: none
  - Description: Dashboard with key statistics; extra actions visible to Librarian/Admin.

- GET `/about`
  - Auth: not required
  - Role: none
  - Description: About page.

## Authentication

- GET/POST `/auth/login`
  - Auth: not required
  - Description: Sign in with username and password. Supports "remember me".

- GET `/auth/logout`
  - Auth: required
  - Description: Sign out of the application.

- GET/POST `/auth/register`
  - Auth: not required
  - Description: Register a new member account.

- GET/POST `/auth/profile`
  - Auth: required
  - Description: View/update your profile (name, email).

- GET/POST `/auth/change-password`
  - Auth: required
  - Description: Change current user password.

## Catalog

- GET `/catalog/books`
  - Auth: required
  - Description: Browse/search books.
  - Query params:
    - `query`: search title/author/isbn
    - `category_id`: filter by category id
    - `availability`: `all|available|unavailable`
    - `page`: pagination (20 per page)

- GET `/catalog/books/<book_id>`
  - Auth: required
  - Description: Book detail page.

- GET/POST `/catalog/books/add`
  - Auth: required
  - Role: Librarian/Admin
  - Description: Add a new book.

- GET/POST `/catalog/books/<book_id>/edit`
  - Auth: required
  - Role: Librarian/Admin
  - Description: Edit a book.

- POST `/catalog/books/<book_id>/delete`
  - Auth: required
  - Role: Librarian/Admin
  - Description: Delete a book (blocked if active loans).

- GET `/catalog/categories`
  - Auth: required
  - Role: Librarian/Admin
  - Description: List all categories.

- GET/POST `/catalog/categories/add`
  - Auth: required
  - Role: Librarian/Admin
  - Description: Add a new category.

- GET/POST `/catalog/categories/<category_id>/edit`
  - Auth: required
  - Role: Librarian/Admin
  - Description: Edit a category.

- POST `/catalog/categories/<category_id>/delete`
  - Auth: required
  - Role: Librarian/Admin
  - Description: Delete a category (only if empty).

## Members

- GET `/members/` or `/members/list`
  - Auth: required
  - Role: Librarian/Admin
  - Description: Browse/search members.
  - Query params:
    - `query`: search name/email/member_id
    - `status`: `all|active|suspended|expired`
    - `page`: pagination (20 per page)

- GET `/members/<member_id>`
  - Auth: required
  - Role: Librarian/Admin
  - Description: Member detail and stats.

- GET/POST `/members/register`
  - Auth: required
  - Role: Librarian/Admin
  - Description: Register a new member.

- GET/POST `/members/<member_id>/edit`
  - Auth: required
  - Role: Librarian/Admin
  - Description: Edit member information.

- POST `/members/<member_id>/delete`
  - Auth: required
  - Role: Librarian/Admin
  - Description: Delete member (blocked if active loans).

- POST `/members/<member_id>/status/<new_status>`
  - Auth: required
  - Role: Librarian/Admin
  - Description: Change member status to `active|suspended|expired`.

## Circulation

- GET `/circulation/loans`
  - Auth: required
  - Role: Librarian/Admin
  - Description: Browse/search/filter loans.
  - Query params:
    - `query`: search by book title or member name
    - `status`: `all|borrowed|returned|overdue`
    - `member_id`: filter by member id
    - `page`: pagination (20 per page)

- GET `/circulation/loans/<loan_id>`
  - Auth: required
  - Role: Librarian/Admin
  - Description: Loan detail.

- GET/POST `/circulation/borrow`
  - Auth: required
  - Role: Librarian/Admin
  - Description: Issue/borrow a book to a member.

- GET/POST `/circulation/return`
  - Auth: required
  - Role: Librarian/Admin
  - Description: Return a borrowed book, compute fines if overdue.

- GET `/circulation/overdue`
  - Auth: required
  - Role: Librarian/Admin
  - Description: List all overdue loans with total unpaid fines.

- GET/POST `/circulation/loans/<loan_id>/pay-fine`
  - Auth: required
  - Role: Librarian/Admin
  - Description: Record fine payment for a loan.

- GET `/circulation/loans/<loan_id>/receipt`
  - Auth: required
  - Role: Librarian/Admin
  - Description: Printable fine payment receipt.

- POST `/circulation/loans/<loan_id>/return`
  - Auth: required
  - Role: Librarian/Admin
  - Description: Quick return of a loan (today).

- GET `/circulation/member/<member_id>/fines`
  - Auth: required
  - Role: Librarian/Admin
  - Description: Member fines overview and breakdown.

- GET `/circulation/member/<member_id>/history`
  - Auth: required
  - Role: Librarian/Admin
  - Description: Member borrowing history.

- GET `/circulation/book/<book_id>/history`
  - Auth: required
  - Role: Librarian/Admin
  - Description: Book loan history.

## Reports & Exports

- GET `/reports/` or `/reports/dashboard`
  - Auth: required
  - Role: Librarian/Admin
  - Description: Reports dashboard with key charts.

- GET `/reports/most-borrowed`
  - Auth: required
  - Role: Librarian/Admin
  - Description: Most borrowed books in a date range.

- GET `/reports/active-members`
  - Auth: required
  - Role: Librarian/Admin
  - Description: Active members and top borrowers in a date range.

- GET `/reports/overdue-summary`
  - Auth: required
  - Role: Librarian/Admin
  - Description: Overdue overview by member and by days range.

- GET `/reports/collection-stats`
  - Auth: required
  - Role: Librarian/Admin
  - Description: Collection statistics (by category, availability).

- GET `/reports/circulation-trends`
  - Auth: required
  - Role: Librarian/Admin
  - Description: Circulation trends over time with date filter.

- GET `/reports/most-borrowed/export/csv`
  - Auth: required
  - Role: Librarian/Admin
  - Description: CSV export for most borrowed books.

- GET `/reports/most-borrowed/export/pdf`
  - Auth: required
  - Role: Librarian/Admin
  - Description: PDF export for most borrowed books.

- GET `/reports/active-members/export/csv`
  - Auth: required
  - Role: Librarian/Admin
  - Description: CSV export for active members top borrowers.

- GET `/reports/collection-stats/export/pdf`
  - Auth: required
  - Role: Librarian/Admin
  - Description: PDF export for collection stats.

- GET `/reports/api/chart-data/<chart_type>`
  - Auth: required
  - Role: Librarian/Admin
  - Description: JSON for charts (`circulation-trends`, `books-by-category`).

## Error Pages

The app provides friendly error pages for: 400, 401, 403, 404, 429, 500. In development, full tracebacks are shown; in production, user-friendly pages are displayed.

---

For any questions or to request additional docs (e.g., request/response schemas), let us know.
