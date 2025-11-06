from datetime import datetime
from app.extensions import db


class Book(db.Model):
    __tablename__ = 'books'

    id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String(13), unique=True, nullable=True, index=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    author = db.Column(db.String(200), nullable=False, index=True)
    publisher = db.Column(db.String(200), nullable=True)
    publication_year = db.Column(db.Integer, nullable=True)
    edition = db.Column(db.String(50), nullable=True)
    language = db.Column(db.String(50), nullable=True, default='English')
    pages = db.Column(db.Integer, nullable=True)
    description = db.Column(db.Text, nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True, index=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    shelf_location = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Circulation relationship: one book has many loans
    loans = db.relationship('Loan', backref='book', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def is_available(self) -> bool:
        return self.available_quantity > 0

    @property
    def available_quantity(self) -> int:
        try:
            # Lazy import to avoid circular dependency at import time
            from app.models.loan import LoanStatus  # type: ignore
        except Exception:
            LoanStatus = None  # fallback if import cycle during migrations
        active_loans_count = 0
        if hasattr(self, 'loans') and self.loans is not None and LoanStatus is not None:
            active_loans_count = self.loans.filter_by(status=LoanStatus.BORROWED).count()
        qty = self.quantity or 0
        return max(0, qty - (active_loans_count or 0))

    def __repr__(self) -> str:
        return f"<Book {self.title} by {self.author}>"

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'isbn': self.isbn,
            'title': self.title,
            'author': self.author,
            'publisher': self.publisher,
            'publication_year': self.publication_year,
            'edition': self.edition,
            'language': self.language,
            'pages': self.pages,
            'description': self.description,
            'category_id': self.category_id,
            'category': getattr(self.category, 'name', None) if hasattr(self, 'category') else None,
            'quantity': self.quantity,
            'shelf_location': self.shelf_location,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
