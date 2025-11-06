from datetime import datetime
from app.extensions import db


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    books = db.relationship(
        'Book', backref='category', lazy='dynamic', cascade='all, delete-orphan'
    )

    @property
    def book_count(self) -> int:
        return self.books.count()

    def __repr__(self) -> str:
        return f"<Category {self.name}>"
