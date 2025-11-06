from datetime import date, timedelta

from flask_wtf import FlaskForm
from wtforms import SelectField, DateField, TextAreaField, SubmitField, HiddenField, StringField, DecimalField
from wtforms.validators import DataRequired, Optional, ValidationError, NumberRange
from decimal import Decimal

from app.models import Book, Member, MemberStatus, Loan, LoanStatus


class BorrowForm(FlaskForm):
    member_id = SelectField('Member', coerce=int, validators=[DataRequired()])
    book_id = SelectField('Book', coerce=int, validators=[DataRequired()])
    due_date = DateField('Due Date (optional)', format='%Y-%m-%d', validators=[Optional()])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Issue Book')

    def validate_member_id(self, member_id):
        member = Member.query.get(member_id.data)
        if not member:
            raise ValidationError('Invalid member selected.')
        can_borrow, reason = member.can_borrow()
        if not can_borrow:
            raise ValidationError(reason or 'Member cannot borrow at this time.')

    def validate_book_id(self, book_id):
        book = Book.query.get(book_id.data)
        if not book:
            raise ValidationError('Invalid book selected.')
        if not book.is_available:
            raise ValidationError('This book is currently unavailable.')
        existing = Loan.query.filter_by(book_id=book_id.data, member_id=self.member_id.data, status=LoanStatus.BORROWED).first()
        if existing:
            raise ValidationError('This member already has an active loan for this book.')

    def validate_due_date(self, due_date):
        if due_date.data:
            if due_date.data < date.today():
                raise ValidationError('Due date cannot be in the past.')
            if due_date.data > date.today() + timedelta(days=90):
                raise ValidationError('Due date cannot be more than 90 days in the future.')


class ReturnForm(FlaskForm):
    loan_id = HiddenField(validators=[DataRequired()])
    return_date = DateField('Return Date', format='%Y-%m-%d', validators=[Optional()], default=date.today)
    notes = TextAreaField('Return Notes', validators=[Optional()])
    submit = SubmitField('Mark as Returned')

    def validate_loan_id(self, loan_id):
        loan = Loan.query.get(loan_id.data)
        if not loan:
            raise ValidationError('Invalid loan selected.')
        if loan.status != LoanStatus.BORROWED:
            raise ValidationError('This loan has already been returned.')

    def validate_return_date(self, return_date):
        if return_date.data:
            loan = Loan.query.get(self.loan_id.data)
            if loan and return_date.data < loan.borrow_date:
                raise ValidationError('Return date cannot be before borrow date.')
            if return_date.data > date.today():
                raise ValidationError('Return date cannot be in the future.')


class LoanSearchForm(FlaskForm):
    query = StringField('Search', validators=[Optional()])
    status = SelectField('Status', coerce=str, validators=[Optional()], default='all')
    member_id = SelectField('Member', coerce=int, validators=[Optional()], default=0)
    submit = SubmitField('Search')


class FinePaymentForm(FlaskForm):
    loan_id = HiddenField(validators=[DataRequired()])
    amount = DecimalField('Payment Amount ($)', places=2, validators=[DataRequired(), NumberRange(min=0.01, message='Amount must be greater than zero')])
    payment_method = SelectField('Payment Method', coerce=str, validators=[Optional()], default='cash', choices=[('cash', 'Cash'), ('card', 'Credit/Debit Card'), ('check', 'Check'), ('other', 'Other')])
    notes = TextAreaField('Payment Notes', validators=[Optional()])
    submit = SubmitField('Record Payment')

    def validate_loan_id(self, loan_id):
        from app.models import Loan
        loan = Loan.query.get(loan_id.data)
        if not loan:
            raise ValidationError('Invalid loan selected.')
        if hasattr(loan, 'fine_balance') and loan.fine_balance <= Decimal('0.00'):
            raise ValidationError('This loan has no outstanding fines.')

    def validate_amount(self, amount):
        from app.models import Loan
        loan = Loan.query.get(self.loan_id.data)
        if loan and amount.data is not None:
            try:
                amt = Decimal(str(amount.data))
            except Exception:
                raise ValidationError('Invalid amount.')
            if hasattr(loan, 'fine_balance') and amt > loan.fine_balance:
                raise ValidationError(f'Amount cannot exceed outstanding balance of ${loan.fine_balance:.2f}.')
