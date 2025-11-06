from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, SelectField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, NumberRange, ValidationError
from app.models import Book, Category


class BookForm(FlaskForm):
    isbn = StringField('ISBN', validators=[Optional(), Length(max=13)])
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    author = StringField('Author', validators=[DataRequired(), Length(max=200)])
    publisher = StringField('Publisher', validators=[Optional(), Length(max=200)])
    publication_year = IntegerField('Publication Year', validators=[Optional(), NumberRange(min=1000, max=9999)])
    edition = StringField('Edition', validators=[Optional(), Length(max=50)])
    language = StringField('Language', validators=[Optional(), Length(max=50)], default='English')
    pages = IntegerField('Pages', validators=[Optional(), NumberRange(min=1)])
    description = TextAreaField('Description', validators=[Optional()])
    category_id = SelectField('Category', coerce=int, validators=[Optional()])
    quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=1)], default=1)
    shelf_location = StringField('Shelf Location', validators=[Optional(), Length(max=50)])
    submit = SubmitField('Save Book')

    def validate_isbn(self, isbn):
        if isbn.data:
            existing = Book.query.filter_by(isbn=isbn.data).first()
            current = getattr(self, '_obj', None)
            if existing and (not current or existing.id != getattr(current, 'id', None)):
                raise ValidationError('A book with this ISBN already exists.')


class CategoryForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Optional()])
    submit = SubmitField('Save Category')

    def validate_name(self, name):
        if name.data:
            existing = Category.query.filter(Category.name.ilike(name.data)).first()
            current = getattr(self, '_obj', None)
            if existing and (not current or existing.id != getattr(current, 'id', None)):
                raise ValidationError('A category with this name already exists.')


class SearchForm(FlaskForm):
    query = StringField('Search', validators=[Optional()])
    category_id = SelectField('Category', coerce=int, validators=[Optional()])
    availability = SelectField(
        'Availability',
        choices=[('all', 'All Books'), ('available', 'Available Only'), ('unavailable', 'Unavailable')],
        default='all',
    )
    submit = SubmitField('Search')
