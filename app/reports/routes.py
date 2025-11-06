from datetime import date, timedelta

from flask import render_template, request, url_for
from flask_login import login_required, current_user

from app.reports import bp
from app.auth.decorators import librarian_required
from app.reports.forms import DateRangeForm
from app.reports import utils


def _parse_dates_from_request(default_days=None):
    s = request.args.get('start_date')
    e = request.args.get('end_date')
    start_date = date.fromisoformat(s) if s else None
    end_date = date.fromisoformat(e) if e else None
    if default_days is not None and not (start_date and end_date):
        start_date, end_date = utils.get_date_range(days=default_days)
    return start_date, end_date


@bp.route('/')
@bp.route('/dashboard')
@login_required
@librarian_required
def dashboard():
    # Overview stats (basic, reuse logic similar to main index)
    from app.models import Book, Member, Loan, LoanStatus, MemberStatus, Category
    total_books = Book.query.count()
    active_members = Member.query.filter_by(status=MemberStatus.ACTIVE).count()
    books_on_loan = Loan.query.filter(Loan.status == LoanStatus.BORROWED).count()
    overdue_books = Loan.query.filter(Loan.status == LoanStatus.BORROWED, Loan.due_date < date.today()).count()

    # Trends last 30 days
    s30, e30 = utils.get_date_range(days=30)
    trend_rows = utils.get_circulation_trends(s30, e30)
    trend_labels = [d.strftime('%Y-%m-%d') for d, _ in trend_rows]
    trend_values = [c for _, c in trend_rows]

    # Books by category
    cat_rows = utils.get_collection_statistics()['by_category']
    cat_labels = [name for name, _ in cat_rows]
    cat_values = [count for _, count in cat_rows]

    return render_template(
        'reports/dashboard.html',
        stats={
            'total_books': total_books,
            'active_members': active_members,
            'books_on_loan': books_on_loan,
            'overdue_books': overdue_books,
        },
        circulation_trend_data={'labels': trend_labels, 'values': trend_values},
        books_by_category_data={'labels': cat_labels, 'values': cat_values},
    )


@bp.route('/most-borrowed')
@login_required
@librarian_required
def most_borrowed():
    form = DateRangeForm(request.args)
    if not (form.start_date.data and form.end_date.data):
        s, e = utils.get_date_range(days=30)
        form.start_date.data, form.end_date.data = s, e
    data = utils.get_most_borrowed_books(form.start_date.data, form.end_date.data, limit=20)
    labels = [b.title for (b, c) in data]
    values = [int(c) for (b, c) in data]
    return render_template('reports/most_borrowed.html', form=form, data=data, chart_data={'labels': labels, 'values': values})


@bp.route('/active-members')
@login_required
@librarian_required
def active_members():
    form = DateRangeForm(request.args)
    if not (form.start_date.data and form.end_date.data):
        s, e = utils.get_date_range(days=30)
        form.start_date.data, form.end_date.data = s, e
    stats = utils.get_active_members_stats(form.start_date.data, form.end_date.data)
    labels = [m.name for (m, c) in stats['top_borrowers']]
    values = [int(c) for (m, c) in stats['top_borrowers']]
    return render_template('reports/active_members.html', form=form, stats=stats, chart_data={'labels': labels, 'values': values})


@bp.route('/overdue-summary')
@login_required
@librarian_required
def overdue_summary():
    summary = utils.get_overdue_summary()
    by_member_labels = list(summary['overdue_by_member'].keys())
    by_member_values = list(summary['overdue_by_member'].values())
    ranges_labels = list(summary['overdue_by_days'].keys())
    ranges_values = list(summary['overdue_by_days'].values())
    return render_template(
        'reports/overdue_summary.html',
        summary=summary,
        overdue_by_member={'labels': by_member_labels, 'values': by_member_values},
        overdue_by_days={'labels': ranges_labels, 'values': ranges_values},
    )


@bp.route('/collection-stats')
@login_required
@librarian_required
def collection_stats():
    stats = utils.get_collection_statistics()
    cat_labels = [name for name, _ in stats['by_category']]
    cat_values = [count for _, count in stats['by_category']]
    availability_labels = ['Available', 'On Loan']
    availability_values = [stats['available'], stats['on_loan']]
    return render_template('reports/collection_stats.html', stats=stats, books_by_category={'labels': cat_labels, 'values': cat_values}, availability={'labels': availability_labels, 'values': availability_values})


@bp.route('/circulation-trends')
@login_required
@librarian_required
def circulation_trends():
    form = DateRangeForm(request.args)
    if not (form.start_date.data and form.end_date.data):
        s, e = utils.get_date_range(days=90)
        form.start_date.data, form.end_date.data = s, e
    rows = utils.get_circulation_trends(form.start_date.data, form.end_date.data)
    labels = [d.strftime('%Y-%m-%d') for d, _ in rows]
    values = [int(c) for _, c in rows]
    total = sum(values) if values else 0
    avg = round(total / max(len(values), 1), 2)
    peak_idx = values.index(max(values)) if values else 0
    peak_day = labels[peak_idx] if values else None
    return render_template('reports/circulation_trends.html', form=form, stats={'total_loans': total, 'avg_per_day': avg, 'peak_day': peak_day, 'peak_count': (max(values) if values else 0)}, chart_data={'labels': labels, 'values': values})


@bp.route('/most-borrowed/export/csv')
@login_required
@librarian_required
def export_most_borrowed_csv():
    start_date, end_date = _parse_dates_from_request(default_days=30)
    rows = utils.get_most_borrowed_books(start_date, end_date, limit=100)
    data = []
    for book, count in rows:
        data.append([book.title, getattr(book, 'author', ''), getattr(book.category, 'name', 'Uncategorized'), int(count)])
    filename = f"most_borrowed_books_{(end_date or date.today()).isoformat()}.csv"
    return utils.export_to_csv(data, headers=['Title', 'Author', 'Category', 'Times Borrowed'], filename=filename)


@bp.route('/most-borrowed/export/pdf')
@login_required
@librarian_required
def export_most_borrowed_pdf():
    start_date, end_date = _parse_dates_from_request(default_days=30)
    rows = utils.get_most_borrowed_books(start_date, end_date, limit=100)
    html = render_template('reports/most_borrowed_pdf.html', start_date=start_date, end_date=end_date, today=date.today(), rows=rows)
    filename = f"most_borrowed_books_{(end_date or date.today()).isoformat()}.pdf"
    return utils.export_to_pdf(html, filename)


@bp.route('/active-members/export/csv')
@login_required
@librarian_required
def export_active_members_csv():
    start_date, end_date = _parse_dates_from_request(default_days=30)
    stats = utils.get_active_members_stats(start_date, end_date)
    rows = []
    for member, total in stats['top_borrowers']:
        rows.append([member.member_id, member.name, member.email or '', int(total)])
    filename = f"active_members_{(end_date or date.today()).isoformat()}.csv"
    return utils.export_to_csv(rows, headers=['Member ID', 'Name', 'Email', 'Total Loans'], filename=filename)


@bp.route('/collection-stats/export/pdf')
@login_required
@librarian_required
def export_collection_stats_pdf():
    stats = utils.get_collection_statistics()
    # Reuse the HTML from the collection_stats page for PDF-friendly simple table
    html = render_template('reports/collection_stats.html', stats=stats, books_by_category={'labels': [n for n, _ in stats['by_category']],'values': [c for _, c in stats['by_category']]}, availability={'labels': ['Available', 'On Loan'], 'values': [stats['available'], stats['on_loan']]})
    filename = f"collection_stats_{date.today().isoformat()}.pdf"
    return utils.export_to_pdf(html, filename)


@bp.route('/api/chart-data/<chart_type>')
@login_required
@librarian_required
def chart_data(chart_type):
    start_date, end_date = _parse_dates_from_request()
    if chart_type == 'circulation-trends':
        if not (start_date and end_date):
            start_date, end_date = utils.get_date_range(days=30)
        rows = utils.get_circulation_trends(start_date, end_date)
        return {'labels': [d.strftime('%Y-%m-%d') for d, _ in rows], 'values': [int(c) for _, c in rows]}
    if chart_type == 'books-by-category':
        stats = utils.get_collection_statistics()
        return {'labels': [n for n, _ in stats['by_category']], 'values': [int(c) for _, c in stats['by_category']]}
    return {'labels': [], 'values': []}
