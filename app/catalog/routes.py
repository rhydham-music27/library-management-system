from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required
from sqlalchemy import or_

from app.extensions import db
from app.models import Book, Category, Loan, LoanStatus
from app.auth.decorators import librarian_required
from . import bp
from .forms import BookForm, CategoryForm, SearchForm


# ===== Book Routes =====
@bp.route('/books')
@login_required
def books():
    page = request.args.get('page', 1, type=int)
    q = request.args.get('query', '', type=str)
    category_id = request.args.get('category_id', 0, type=int)
    availability = request.args.get('availability', 'all', type=str)

    base_query = Book.query
    if q:
        like = f"%{q}%"
        base_query = base_query.filter(or_(Book.title.ilike(like), Book.author.ilike(like), Book.isbn.ilike(like)))
    if category_id and category_id != 0:
        base_query = base_query.filter(Book.category_id == category_id)
    if availability == 'available':
        base_query = base_query.filter(Book.quantity > 0)
    elif availability == 'unavailable':
        base_query = base_query.filter(Book.quantity == 0)

    base_query = base_query.order_by(Book.title.asc())
    pagination = base_query.paginate(page=page, per_page=20, error_out=False)

    # Populate search form
    form = SearchForm(request.args)
    categories = Category.query.order_by(Category.name.asc()).all()
    form.category_id.choices = [(0, 'All Categories')] + [(c.id, c.name) for c in categories]

    return render_template('catalog/books.html', pagination=pagination, form=form, query=q, category_id=category_id, availability=availability)


@bp.route('/books/<int:book_id>')
@login_required
def book_detail(book_id):
    book = Book.query.get_or_404(book_id)
    return render_template('catalog/book_detail.html', book=book)


@bp.route('/books/add', methods=['GET', 'POST'])
@login_required
@librarian_required
def add_book():
    form = BookForm()
    categories = Category.query.order_by(Category.name.asc()).all()
    form.category_id.choices = [(0, '-- Select Category --')] + [(c.id, c.name) for c in categories]
    if form.validate_on_submit():
        book = Book(
            isbn=form.isbn.data or None,
            title=form.title.data,
            author=form.author.data,
            publisher=form.publisher.data or None,
            publication_year=form.publication_year.data,
            edition=form.edition.data or None,
            language=form.language.data or 'English',
            pages=form.pages.data,
            description=form.description.data or None,
            category_id=form.category_id.data or None if form.category_id.data != 0 else None,
            quantity=form.quantity.data,
            shelf_location=form.shelf_location.data or None,
        )
        db.session.add(book)
        db.session.commit()
        flash(f'Book "{book.title}" added successfully.', 'success')
        return redirect(url_for('catalog.book_detail', book_id=book.id))
    return render_template('catalog/book_form.html', form=form, title='Add New Book')


@bp.route('/books/<int:book_id>/edit', methods=['GET', 'POST'])
@login_required
@librarian_required
def edit_book(book_id):
    book = Book.query.get_or_404(book_id)
    form = BookForm(obj=book)
    # pass current object for validators
    form._obj = book
    categories = Category.query.order_by(Category.name.asc()).all()
    form.category_id.choices = [(0, '-- Select Category --')] + [(c.id, c.name) for c in categories]

    if request.method == 'GET':
        form.category_id.data = book.category_id or 0

    if form.validate_on_submit():
        book.isbn = form.isbn.data or None
        book.title = form.title.data
        book.author = form.author.data
        book.publisher = form.publisher.data or None
        book.publication_year = form.publication_year.data
        book.edition = form.edition.data or None
        book.language = form.language.data or 'English'
        book.pages = form.pages.data
        book.description = form.description.data or None
        book.category_id = form.category_id.data or None if form.category_id.data != 0 else None
        book.quantity = form.quantity.data
        book.shelf_location = form.shelf_location.data or None
        db.session.commit()
        flash('Book updated successfully.', 'success')
        return redirect(url_for('catalog.book_detail', book_id=book.id))

    return render_template('catalog/book_form.html', form=form, title='Edit Book', book=book)


@bp.route('/books/<int:book_id>/delete', methods=['POST'])
@login_required
@librarian_required
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    title = book.title
    # Prevent deleting books with active loans
    active_loans = 0
    try:
        active_loans = book.loans.filter_by(status=LoanStatus.BORROWED).count()
    except Exception:
        active_loans = 0
    if active_loans > 0:
        flash(f'Cannot delete book "{title}" because it has {active_loans} active loan(s). Please return all copies first.', 'warning')
        return redirect(url_for('catalog.book_detail', book_id=book.id))
    db.session.delete(book)
    db.session.commit()
    flash(f'Book "{title}" deleted successfully.', 'success')
    return redirect(url_for('catalog.books'))


# ===== Category Routes =====
@bp.route('/categories')
@login_required
@librarian_required
def categories():
    cats = Category.query.order_by(Category.name.asc()).all()
    return render_template('catalog/categories.html', categories=cats)


@bp.route('/categories/add', methods=['GET', 'POST'])
@login_required
@librarian_required
def add_category():
    form = CategoryForm()
    if form.validate_on_submit():
        cat = Category(name=form.name.data.strip(), description=form.description.data or None)
        db.session.add(cat)
        db.session.commit()
        flash('Category added successfully.', 'success')
        return redirect(url_for('catalog.categories'))
    return render_template('catalog/category_form.html', form=form, title='Add New Category')


@bp.route('/categories/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
@librarian_required
def edit_category(category_id):
    cat = Category.query.get_or_404(category_id)
    form = CategoryForm(obj=cat)
    form._obj = cat
    if form.validate_on_submit():
        cat.name = form.name.data.strip()
        cat.description = form.description.data or None
        db.session.commit()
        flash('Category updated successfully.', 'success')
        return redirect(url_for('catalog.categories'))
    return render_template('catalog/category_form.html', form=form, title='Edit Category', category=cat)


@bp.route('/categories/<int:category_id>/delete', methods=['POST'])
@login_required
@librarian_required
def delete_category(category_id):
    cat = Category.query.get_or_404(category_id)
    if cat.books.count() > 0:
        flash('Cannot delete category with books. Move or delete books first.', 'warning')
        return redirect(url_for('catalog.categories'))
    name = cat.name
    db.session.delete(cat)
    db.session.commit()
    flash(f'Category "{name}" deleted successfully.', 'success')
    return redirect(url_for('catalog.categories'))
