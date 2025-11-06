from datetime import datetime, date, timedelta
from enum import Enum

from app.extensions import db
from decimal import Decimal
from flask import current_app


class LoanStatus(Enum):
    BORROWED = "borrowed"
    RETURNED = "returned"


class Loan(db.Model):
    __tablename__ = 'loans'

    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False, index=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False, index=True)
    borrow_date = db.Column(db.Date, nullable=False, default=date.today)
    due_date = db.Column(db.Date, nullable=False)
    return_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.Enum(LoanStatus), nullable=False, default=LoanStatus.BORROWED)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # Fines
    fine_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    fine_paid = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)

    @property
    def is_active(self) -> bool:
        return self.status == LoanStatus.BORROWED

    @property
    def is_overdue(self) -> bool:
        return self.is_active and date.today() > self.due_date

    @property
    def days_overdue(self) -> int:
        if not self.is_overdue:
            return 0
        return (date.today() - self.due_date).days

    @property
    def status_badge_class(self) -> str:
        if self.status == LoanStatus.RETURNED:
            if self.has_unpaid_fines:
                return 'bg-warning'
            return 'bg-success'
        if self.is_overdue:
            return 'bg-danger'
        return 'bg-info'

    @staticmethod
    def calculate_due_date(borrow_date: date, loan_period_days: int = 14) -> date:
        return borrow_date + timedelta(days=loan_period_days)

    def mark_returned(self, return_date: date | None = None) -> None:
        self.return_date = return_date or date.today()
        self.status = LoanStatus.RETURNED

    @property
    def fine_balance(self) -> Decimal:
        return Decimal(str(self.fine_amount or 0)) - Decimal(str(self.fine_paid or 0))

    @property
    def has_unpaid_fines(self) -> bool:
        return self.fine_balance > Decimal('0.00')

    def calculate_fine(self) -> Decimal:
        if not self.is_overdue:
            return Decimal('0.00')
        fine_rate = current_app.config.get('FINE_RATE_PER_DAY', 1.0)
        return Decimal(str(self.days_overdue)) * Decimal(str(fine_rate))

    def update_fine_amount(self) -> Decimal:
        self.fine_amount = self.calculate_fine()
        return self.fine_amount

    def record_fine_payment(self, amount: Decimal, notes: str | None = None) -> tuple[bool, str]:
        try:
            amt = Decimal(str(amount))
        except Exception:
            return False, 'Invalid payment amount.'
        if amt <= Decimal('0.00'):
            return False, 'Amount must be greater than zero.'
        if amt > self.fine_balance:
            return False, f'Amount cannot exceed outstanding balance of ${self.fine_balance:.2f}.'
        self.fine_paid = Decimal(str(self.fine_paid or 0)) + amt
        if notes:
            from datetime import datetime as _dt
            stamp = _dt.now().strftime('%Y-%m-%d %H:%M')
            self.notes = (self.notes + '\n' if self.notes else '') + f"Payment {stamp}: {notes}"
        return True, f'Payment of ${amt:.2f} recorded successfully'

    def is_fine_fully_paid(self) -> bool:
        return self.fine_balance <= Decimal('0.00')

    def __repr__(self) -> str:
        try:
            book_title = getattr(self.book, 'title', 'Unknown')
            member_name = getattr(self.member, 'name', 'Unknown')
        except Exception:
            book_title, member_name = 'Unknown', 'Unknown'
        return f"<Loan: {book_title} to {member_name} ({self.status.value})>"

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'book_id': self.book_id,
            'book_title': getattr(self.book, 'title', None),
            'member_id': self.member_id,
            'member_name': getattr(self.member, 'name', None),
            'borrow_date': self.borrow_date.isoformat() if self.borrow_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'return_date': self.return_date.isoformat() if self.return_date else None,
            'status': self.status.value if self.status else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_overdue': self.is_overdue,
            'days_overdue': self.days_overdue,
            'fine_amount': float(self.fine_amount) if self.fine_amount else 0.0,
            'fine_paid': float(self.fine_paid) if self.fine_paid else 0.0,
            'fine_balance': float(self.fine_balance),
            'has_unpaid_fines': self.has_unpaid_fines,
        }
