from datetime import date

from flask import render_template, redirect, url_for, flash, request, abort, current_app, render_template_string
from flask_login import login_required
from sqlalchemy import or_, func
from decimal import Decimal

from app.extensions import db
from app.auth.decorators import librarian_required
from app.models import Book, Member, MemberStatus, Loan, LoanStatus
from . import bp
from .forms import BorrowForm, ReturnForm, LoanSearchForm, FinePaymentForm


@bp.route('/loans')
@login_required
@librarian_required
def loans():
    page = request.args.get('page', 1, type=int)
    q = request.args.get('query', '', type=str)
    status = request.args.get('status', 'all', type=str)
    member_id = request.args.get('member_id', 0, type=int)

    base_query = Loan.query.join(Book).join(Member)
    if q:
        like = f"%{q}%"
        base_query = base_query.filter(or_(Book.title.ilike(like), Member.name.ilike(like)))
    if status == 'borrowed':
        base_query = base_query.filter(Loan.status == LoanStatus.BORROWED)
    elif status == 'returned':
        base_query = base_query.filter(Loan.status == LoanStatus.RETURNED)
    elif status == 'overdue':
        base_query = base_query.filter(Loan.status == LoanStatus.BORROWED, Loan.due_date < date.today())
    if member_id and member_id != 0:
        base_query = base_query.filter(Loan.member_id == member_id)

    base_query = base_query.order_by(Loan.borrow_date.desc())
    pagination = base_query.paginate(page=page, per_page=20, error_out=False)

    form = LoanSearchForm(request.args)
    members = Member.query.filter_by(status=MemberStatus.ACTIVE).order_by(Member.name.asc()).all()
    form.status.choices = [
        ('all', 'All Loans'),
        ('borrowed', 'Active Loans'),
        ('returned', 'Returned'),
        ('overdue', 'Overdue'),
    ]
    form.member_id.choices = [(0, 'All Members')] + [(m.id, f"{m.name} ({m.member_id})") for m in members]

    return render_template('circulation/loans.html', pagination=pagination, form=form, query=q, status=status, member_id=member_id)


@bp.route('/loans/<int:loan_id>')
@login_required
@librarian_required
def loan_detail(loan_id: int):
    loan = Loan.query.get_or_404(loan_id)
    days_borrowed = ((loan.return_date or date.today()) - loan.borrow_date).days
    return render_template('circulation/loan_detail.html', loan=loan, days_borrowed=days_borrowed, fine_rate=current_app.config.get('FINE_RATE_PER_DAY', 1.0))


@bp.route('/borrow', methods=['GET', 'POST'])
@login_required
@librarian_required
def borrow():
    form = BorrowForm()

    active_members = Member.query.filter_by(status=MemberStatus.ACTIVE).order_by(Member.name.asc()).all()
    form.member_id.choices = [(m.id, f"{m.name} ({m.member_id})") for m in active_members]

    books = Book.query.order_by(Book.title.asc()).all()
    # Show all books but validation ensures availability
    form.book_id.choices = [(b.id, f"{b.title} by {b.author}") for b in books]

    if form.validate_on_submit():
        member = Member.query.get(form.member_id.data)
        book = Book.query.get(form.book_id.data)
        borrow_date = date.today()
        default_days = current_app.config.get('LOAN_PERIOD_DAYS', 14)
        due_date = form.due_date.data or Loan.calculate_due_date(borrow_date, default_days)
        loan = Loan(
            book_id=book.id,
            member_id=member.id,
            borrow_date=borrow_date,
            due_date=due_date,
            status=LoanStatus.BORROWED,
            notes=form.notes.data or None,
        )
        db.session.add(loan)
        db.session.commit()
        flash(f'Book "{book.title}" issued to {member.name}. Due date: {due_date.strftime("%b %d, %Y")}', 'success')
        return redirect(url_for('circulation.loan_detail', loan_id=loan.id))

    # Optional: pre-select book if provided via query param
    pre_book_id = request.args.get('book_id', type=int)
    if request.method == 'GET' and pre_book_id:
        try:
            form.book_id.data = pre_book_id
        except Exception:
            pass

    return render_template('circulation/borrow_form.html', form=form, loan_period_days=current_app.config.get('LOAN_PERIOD_DAYS', 14))


@bp.route('/return', methods=['GET', 'POST'])
@login_required
@librarian_required
def return_book():
    if request.method == 'GET':
        active_loans = Loan.query.filter_by(status=LoanStatus.BORROWED).order_by(Loan.due_date.asc()).all()
        return render_template('circulation/return_form.html', active_loans=active_loans, form=None, fine_rate=current_app.config.get('FINE_RATE_PER_DAY', 1.0))

    # POST: confirm and process
    loan_id = request.form.get('loan_id', type=int) or request.form.get('loan_id')
    if not loan_id:
        flash('No loan selected.', 'warning')
        return redirect(url_for('circulation.return_book'))

    form = ReturnForm()
    form.loan_id.data = int(loan_id)

    if form.validate_on_submit():
        loan = Loan.query.get_or_404(int(form.loan_id.data))
        if loan.status != LoanStatus.BORROWED:
            flash('This loan has already been returned.', 'info')
            return redirect(url_for('circulation.loans'))
        loan.mark_returned(form.return_date.data or date.today())
        if form.notes.data:
            loan.notes = (loan.notes + '\n' if loan.notes else '') + f"Return: {form.notes.data}"
        # Calculate and store fine if any
        loan.update_fine_amount()
        db.session.commit()
        if loan.fine_amount and float(loan.fine_amount) > 0:
            flash(f'Book "{loan.book.title}" returned by {loan.member.name}. Fine assessed: ${loan.fine_amount:.2f} for {loan.days_overdue} day(s) overdue.', 'warning')
        else:
            flash(f'Book "{loan.book.title}" returned by {loan.member.name}.', 'success')
        return redirect(url_for('circulation.loan_detail', loan_id=loan.id))

    # If form didn't validate, render confirmation step with loan displayed
    loan = Loan.query.get(form.loan_id.data) if form.loan_id.data else None
    return render_template('circulation/return_form.html', form=form, loan=loan, active_loans=None, fine_rate=current_app.config.get('FINE_RATE_PER_DAY', 1.0))


@bp.route('/overdue')
@login_required
@librarian_required
def overdue():
    page = request.args.get('page', 1, type=int)
    base_query = (
        Loan.query
        .filter(Loan.status == LoanStatus.BORROWED, Loan.due_date < date.today())
        .join(Book)
        .join(Member)
        .order_by(Loan.due_date.asc())
    )
    pagination = base_query.paginate(page=page, per_page=20, error_out=False)
    total_overdue = pagination.total
    total_fines = (
        db.session.query(func.sum(Loan.fine_amount - Loan.fine_paid))
        .filter(Loan.status == LoanStatus.BORROWED, Loan.due_date < date.today())
        .scalar() or Decimal('0.00')
    )
    return render_template('circulation/overdue.html', pagination=pagination, total_overdue=total_overdue, total_fines=total_fines)


@bp.route('/loans/<int:loan_id>/pay-fine', methods=['GET', 'POST'])
@login_required
@librarian_required
def pay_fine(loan_id: int):
    loan = Loan.query.get_or_404(loan_id)
    if not loan.has_unpaid_fines:
        flash('This loan has no outstanding fines.', 'info')
        return redirect(url_for('circulation.loan_detail', loan_id=loan.id))
    form = FinePaymentForm()
    if request.method == 'GET':
        form.loan_id.data = loan.id
    if form.validate_on_submit():
        amount = Decimal(str(form.amount.data))
        success, message = loan.record_fine_payment(amount, form.notes.data)
        if success:
            db.session.commit()
            flash(message, 'success')
            return redirect(url_for('circulation.fine_receipt', loan_id=loan.id, amount=str(amount), method=form.payment_method.data))
        else:
            flash(message, 'danger')
    return render_template('circulation/fine_payment.html', form=form, loan=loan, fine_rate=current_app.config.get('FINE_RATE_PER_DAY', 1.0))


@bp.route('/loans/<int:loan_id>/receipt')
@login_required
@librarian_required
def fine_receipt(loan_id: int):
    from datetime import date as _date
    loan = Loan.query.get_or_404(loan_id)
    # Parse amount as Decimal for safe arithmetic with DB Numeric fields
    from decimal import Decimal as _Dec
    _amt_str = request.args.get('amount')
    try:
        amount_dec = _Dec(str(_amt_str)) if _amt_str is not None else _Dec('0.00')
    except Exception:
        amount_dec = _Dec('0.00')
    payment_method = request.args.get('method')
    payment_date = _date.today()
    # Precompute numeric values for display to avoid Decimal/float ops in templates
    prev_paid_dec = _Dec(str(loan.fine_paid or 0)) - amount_dec
    fine_balance_dec = _Dec(str(loan.fine_balance or 0))
    return render_template(
        'circulation/fine_receipt.html',
        loan=loan,
        amount=float(amount_dec),
        prev_paid=float(prev_paid_dec),
        fine_balance=float(fine_balance_dec),
        payment_method=payment_method,
        payment_date=payment_date,
        fine_rate=current_app.config.get('FINE_RATE_PER_DAY', 1.0),
    )


@bp.route('/member/<int:member_id>/fines')
@login_required
@librarian_required
def member_fines(member_id: int):
    member = Member.query.get_or_404(member_id)
    loans_with_fines = member.loans.filter(Loan.fine_amount > 0).order_by(Loan.due_date.desc()).all()
    total_fines_assessed = sum([float(l.fine_amount) for l in loans_with_fines]) if loans_with_fines else 0.0
    total_fines_paid = sum([float(l.fine_paid) for l in loans_with_fines]) if loans_with_fines else 0.0
    try:
        total_outstanding = float(member.total_unpaid_fines())
    except Exception:
        total_outstanding = 0.0
    return render_template('circulation/member_fines.html', member=member, loans=loans_with_fines, total_fines_assessed=total_fines_assessed, total_fines_paid=total_fines_paid, total_outstanding=total_outstanding)


@bp.route('/loans/<int:loan_id>/return', methods=['POST'])
@login_required
@librarian_required
def quick_return(loan_id: int):
    loan = Loan.query.get_or_404(loan_id)
    if loan.status != LoanStatus.BORROWED:
        flash('This loan has already been returned.', 'info')
        return redirect(url_for('circulation.loans'))
    loan.mark_returned(date.today())
    db.session.commit()
    flash('Book returned successfully.', 'success')
    return redirect(url_for('circulation.loans'))


@bp.route('/member/<int:member_id>/history')
@login_required
@librarian_required
def member_history(member_id: int):
    member = Member.query.get_or_404(member_id)
    page = request.args.get('page', 1, type=int)
    pagination = member.loans.order_by(Loan.borrow_date.desc()).paginate(page=page, per_page=20, error_out=False)

    total_borrowed = member.loans.count()
    currently_borrowed = member.loans.filter_by(status=LoanStatus.BORROWED).count()
    total_overdue = member.loans.filter(Loan.status == LoanStatus.BORROWED, Loan.due_date < date.today()).count()

    return render_template('circulation/member_history.html', member=member, pagination=pagination, total_borrowed=total_borrowed, currently_borrowed=currently_borrowed, total_overdue=total_overdue)


@bp.route('/book/<int:book_id>/history')
@login_required
@librarian_required
def book_history(book_id: int):
    book = Book.query.get_or_404(book_id)
    page = request.args.get('page', 1, type=int)
    pagination = book.loans.order_by(Loan.borrow_date.desc()).paginate(page=page, per_page=20, error_out=False)

    total_times_borrowed = book.loans.count()
    currently_on_loan = book.loans.filter_by(status=LoanStatus.BORROWED).count()

    return render_template('circulation/book_history.html', book=book, pagination=pagination, total_times_borrowed=total_times_borrowed, currently_on_loan=currently_on_loan)
