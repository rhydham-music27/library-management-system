import csv
import io
from datetime import date, timedelta

from flask import make_response, current_app, request
from sqlalchemy import func

from app.extensions import db
from app.models import Book, Category, Member, MemberStatus, Loan, LoanStatus


def get_date_range(start_date=None, end_date=None, days=30):
    if start_date and end_date:
        return start_date, end_date
    if days is not None:
        return date.today() - timedelta(days=days), date.today()
    return None, None


def get_most_borrowed_books(start_date=None, end_date=None, limit=10):
    q = db.session.query(Book, func.count(Loan.id).label('borrow_count'))\
        .join(Loan, Book.id == Loan.book_id)
    if start_date and end_date:
        q = q.filter(Loan.borrow_date.between(start_date, end_date))
    q = q.group_by(Book.id).order_by(func.count(Loan.id).desc()).limit(limit)
    return q.all()


def get_active_members_stats(start_date=None, end_date=None):
    stats = {
        'total_members': Member.query.count(),
        'active_members': Member.query.filter_by(status=MemberStatus.ACTIVE).count(),
        'members_with_loans': 0,
        'top_borrowers': [],
    }
    loan_q = db.session.query(Loan.member_id).distinct()
    if start_date and end_date:
        loan_q = loan_q.filter(Loan.borrow_date.between(start_date, end_date))
    stats['members_with_loans'] = loan_q.count()

    top_q = db.session.query(Member, func.count(Loan.id).label('loan_count'))\
        .join(Loan, Member.id == Loan.member_id)
    if start_date and end_date:
        top_q = top_q.filter(Loan.borrow_date.between(start_date, end_date))
    top_q = top_q.group_by(Member.id).order_by(func.count(Loan.id).desc()).limit(20)
    stats['top_borrowers'] = top_q.all()
    return stats


def get_overdue_summary():
    today = date.today()
    overdue_loans = Loan.query\
        .filter(Loan.status == LoanStatus.BORROWED, Loan.due_date < today)\
        .join(Book).join(Member).all()

    total_overdue = len(overdue_loans)
    by_member = {}
    days_buckets = {'1-7': 0, '8-14': 0, '15-30': 0, '30+': 0}

    details = []
    for loan in overdue_loans:
        days_overdue = (today - loan.due_date).days
        details.append({
            'loan': loan,
            'book': loan.book,
            'member': loan.member,
            'due_date': loan.due_date,
            'days_overdue': days_overdue,
        })
        key = loan.member.name
        by_member[key] = by_member.get(key, 0) + 1
        if days_overdue <= 7:
            days_buckets['1-7'] += 1
        elif days_overdue <= 14:
            days_buckets['8-14'] += 1
        elif days_overdue <= 30:
            days_buckets['15-30'] += 1
        else:
            days_buckets['30+'] += 1

    unique_members = len(set(d['member'].id for d in details))
    avg_days = 0
    if total_overdue:
        avg_days = sum(d['days_overdue'] for d in details) / total_overdue

    return {
        'total_overdue': total_overdue,
        'unique_members_with_overdue': unique_members,
        'avg_days_overdue': round(avg_days, 1),
        'overdue_by_member': by_member,
        'overdue_by_days': days_buckets,
        'details': details,
    }


def get_collection_statistics():
    total_books = Book.query.count()
    total_quantity = db.session.query(func.sum(Book.quantity)).scalar() or 0
    by_category = db.session.query(Category.name, func.count(Book.id))\
        .join(Book).group_by(Category.id).all()

    on_loan_count = Loan.query.filter(Loan.status == LoanStatus.BORROWED).count()
    available = max(total_quantity - on_loan_count, 0)

    return {
        'total_books': total_books,
        'total_quantity': int(total_quantity),
        'by_category': by_category,
        'available': available,
        'on_loan': on_loan_count,
        'total_categories': Category.query.count(),
        'avg_books_per_category': round(total_books / max(Category.query.count(), 1), 2),
    }


def get_circulation_trends(start_date, end_date):
    q = db.session.query(Loan.borrow_date, func.count(Loan.id).label('cnt'))\
        .filter(Loan.borrow_date.between(start_date, end_date))\
        .group_by(Loan.borrow_date)\
        .order_by(Loan.borrow_date.asc())
    return q.all()


def export_to_csv(data, headers, filename):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    for row in data:
        writer.writerow(row)
    resp = make_response(output.getvalue())
    resp.headers['Content-Type'] = 'text/csv'
    resp.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return resp


def export_to_pdf(html_content, filename):
    try:
        from weasyprint import HTML
    except Exception:  # pragma: no cover - runtime dependency
        HTML = None
    if HTML is None:
        resp = make_response('PDF generation dependency missing', 500)
        return resp
    try:
        # Provide base_url so relative URLs (static files, images, CSS) resolve correctly
        pdf_bytes = HTML(string=html_content, base_url=request.host_url).write_pdf()
    except Exception:
        # Log full traceback for debugging (commonly missing Windows deps for WeasyPrint)
        current_app.logger.exception('WeasyPrint PDF generation failed')
        resp = make_response('PDF generation failed. Check server logs for details.', 500)
        return resp
    resp = make_response(pdf_bytes)
    resp.headers['Content-Type'] = 'application/pdf'
    resp.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return resp
