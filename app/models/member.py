from datetime import datetime, date
from enum import Enum
import random

from app.extensions import db


class MemberStatus(Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"


class Member(db.Model):
    __tablename__ = "members"

    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    registration_date = db.Column(db.Date, nullable=False, default=date.today)
    status = db.Column(db.Enum(MemberStatus), nullable=False, default=MemberStatus.ACTIVE)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Circulation relationship: one member has many loans
    loans = db.relationship('Loan', backref='member', lazy='dynamic', cascade='all, delete-orphan')

    @staticmethod
    def generate_member_id() -> str:
        """Generate a unique member ID like MEM-2025-123456"""
        from datetime import datetime as _dt

        year = _dt.now().year
        for _ in range(10):
            rand_part = random.randint(100000, 999999)
            candidate = f"MEM-{year}-{rand_part}"
            if not Member.query.filter_by(member_id=candidate).first():
                return candidate
        # Fallback with larger random space if collisions persist
        rand_part = random.randint(100000, 999999)
        return f"MEM-{year}-{rand_part}"

    @property
    def is_active(self) -> bool:
        return self.status == MemberStatus.ACTIVE

    @property
    def is_suspended(self) -> bool:
        return self.status == MemberStatus.SUSPENDED

    @property
    def is_expired(self) -> bool:
        return self.status == MemberStatus.EXPIRED

    @property
    def status_badge_class(self) -> str:
        if self.status == MemberStatus.ACTIVE:
            return "bg-success"
        if self.status == MemberStatus.SUSPENDED:
            return "bg-warning text-dark"
        return "bg-secondary"

    def __repr__(self) -> str:
        return f"<Member {self.member_id}: {self.name}>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "member_id": self.member_id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
            "registration_date": self.registration_date.isoformat() if self.registration_date else None,
            "status": self.status.value if self.status else None,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def activate(self) -> None:
        self.status = MemberStatus.ACTIVE

    def suspend(self) -> None:
        self.status = MemberStatus.SUSPENDED

    def expire(self) -> None:
        self.status = MemberStatus.EXPIRED

    # ===== Circulation helpers =====
    def active_loans_count(self) -> int:
        try:
            from app.models.loan import LoanStatus  # type: ignore
        except Exception:
            return 0
        return self.loans.filter_by(status=LoanStatus.BORROWED).count()

    def has_overdue_loans(self) -> bool:
        try:
            from app.models.loan import Loan, LoanStatus  # type: ignore
        except Exception:
            return False
        return (
            self.loans
            .filter(Loan.status == LoanStatus.BORROWED, Loan.due_date < date.today())
            .count() > 0
        )

    def has_unpaid_fines(self) -> bool:
        try:
            from app.models.loan import Loan  # type: ignore
        except Exception:
            return False
        return self.loans.filter(Loan.fine_amount > Loan.fine_paid).count() > 0

    def total_unpaid_fines(self):
        try:
            from app.models.loan import Loan  # type: ignore
            from sqlalchemy import func
        except Exception:
            return 0
        result = (
            db.session.query(func.sum(Loan.fine_amount - Loan.fine_paid))
            .filter(Loan.member_id == self.id, Loan.fine_amount > Loan.fine_paid)
            .scalar()
        )
        return (result or 0)

    def can_borrow(self) -> tuple[bool, str | None]:
        from flask import current_app
        if not self.is_active:
            return False, 'Member is not active.'
        if self.has_overdue_loans():
            return False, 'Member has overdue books.'
        if self.has_unpaid_fines():
            total = self.total_unpaid_fines()
            return False, f'Member has unpaid fines totaling ${total:.2f}.'
        max_active = current_app.config.get('MAX_ACTIVE_LOANS', 5)
        if self.active_loans_count() >= max_active:
            return False, f'Member has reached the limit of {max_active} active loans.'
        return True, None
