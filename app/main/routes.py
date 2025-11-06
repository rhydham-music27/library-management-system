from flask import render_template
from . import bp
from app.models import Book, Category, Member, MemberStatus, Loan, LoanStatus
from datetime import date
from sqlalchemy import func
from decimal import Decimal


@bp.route("/")
@bp.route("/index")
def index():
    stats = {
        "total_books": Book.query.count(),
        "active_members": Member.query.filter_by(status=MemberStatus.ACTIVE).count(),
        "books_on_loan": Loan.query.filter_by(status=LoanStatus.BORROWED).count(),
        "overdue_books": Loan.query.filter(Loan.status == LoanStatus.BORROWED, Loan.due_date < date.today()).count(),
    }
    unpaid_fines_query = (
        Book.query.session.query(func.sum(Loan.fine_amount - Loan.fine_paid))
        .filter(Loan.fine_amount > Loan.fine_paid)
        .scalar()
    )
    stats['total_unpaid_fines'] = float(unpaid_fines_query or 0)
    recent_books = Book.query.order_by(Book.created_at.desc()).limit(5).all()
    recent_members = Member.query.order_by(Member.registration_date.desc()).limit(5).all()
    recent_loans = Loan.query.filter_by(status=LoanStatus.BORROWED).order_by(Loan.borrow_date.desc()).limit(5).all()
    overdue_with_fines = (
        Loan.query
        .filter(Loan.status == LoanStatus.BORROWED, Loan.due_date < date.today(), Loan.fine_amount > Loan.fine_paid)
        .order_by(Loan.due_date.asc())
        .limit(5)
        .all()
    )
    return render_template("main/index.html", stats=stats, recent_books=recent_books, recent_members=recent_members, recent_loans=recent_loans, overdue_with_fines=overdue_with_fines, message="Welcome to the Library Management System!")


@bp.route("/about")
def about():
    return render_template("main/about.html")
