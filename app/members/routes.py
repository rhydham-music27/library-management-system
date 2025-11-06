from datetime import date

from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required
from sqlalchemy import or_

from app.extensions import db
from app.auth.decorators import librarian_required
from app.models import Member, MemberStatus, Loan, LoanStatus
from . import bp
from .forms import MemberForm, MemberSearchForm


@bp.route('/')
@bp.route('/list')
@login_required
@librarian_required
def members():
    page = request.args.get('page', 1, type=int)
    q = request.args.get('query', '', type=str)
    status = request.args.get('status', 'all', type=str)

    base_query = Member.query
    if q:
        like = f"%{q}%"
        base_query = base_query.filter(
            or_(
                Member.name.ilike(like),
                Member.email.ilike(like),
                Member.member_id.ilike(like),
            )
        )
    if status and status != 'all':
        try:
            st = MemberStatus[status.upper()]
            base_query = base_query.filter(Member.status == st)
        except KeyError:
            pass

    base_query = base_query.order_by(Member.registration_date.desc())
    pagination = base_query.paginate(page=page, per_page=20, error_out=False)

    form = MemberSearchForm(request.args)

    return render_template(
        'members/members.html',
        pagination=pagination,
        form=form,
        query=q,
        status=status,
    )


@bp.route('/<int:member_id>')
@login_required
@librarian_required
def member_detail(member_id: int):
    member = Member.query.get_or_404(member_id)

    # Circulation stats
    total_borrowed = member.loans.count()
    currently_borrowed = member.loans.filter_by(status=LoanStatus.BORROWED).count()
    overdue_books = member.loans.filter(Loan.status == LoanStatus.BORROWED, Loan.due_date < date.today()).count()

    return render_template(
        'members/member_detail.html',
        member=member,
        total_borrowed=total_borrowed,
        currently_borrowed=currently_borrowed,
        overdue_books=overdue_books,
    )


@bp.route('/register', methods=['GET', 'POST'])
@login_required
@librarian_required
def register():
    form = MemberForm()
    if form.validate_on_submit():
        mid = Member.generate_member_id()
        member = Member(
            member_id=mid,
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data or None,
            address=form.address.data or None,
            registration_date=date.today(),
            status=MemberStatus[form.status.data.upper()],
            notes=form.notes.data or None,
        )
        db.session.add(member)
        db.session.commit()
        flash(f'Member registered successfully. Member ID: {member.member_id}', 'success')
        return redirect(url_for('members.member_detail', member_id=member.id))
    return render_template('members/member_form.html', form=form, title='Register New Member')


@bp.route('/<int:member_id>/edit', methods=['GET', 'POST'])
@login_required
@librarian_required
def edit_member(member_id: int):
    member = Member.query.get_or_404(member_id)
    form = MemberForm(obj=member)
    form._obj = member  # for validators

    if form.validate_on_submit():
        member.name = form.name.data
        member.email = form.email.data
        member.phone = form.phone.data or None
        member.address = form.address.data or None
        member.status = MemberStatus[form.status.data.upper()]
        member.notes = form.notes.data or None
        db.session.commit()
        flash('Member information updated successfully.', 'success')
        return redirect(url_for('members.member_detail', member_id=member.id))

    return render_template('members/member_form.html', form=form, title='Edit Member', member=member)


@bp.route('/<int:member_id>/delete', methods=['POST'])
@login_required
@librarian_required
def delete_member(member_id: int):
    member = Member.query.get_or_404(member_id)
    # Prevent delete if active loans
    if member.loans.filter_by(status=LoanStatus.BORROWED).count() > 0:
        flash('Cannot delete member with active loans. Please return all books first.', 'warning')
        return redirect(url_for('members.member_detail', member_id=member.id))
    mid, name = member.member_id, member.name
    db.session.delete(member)
    db.session.commit()
    flash(f'Member {mid} ({name}) deleted successfully.', 'success')
    return redirect(url_for('members.members'))


@bp.route('/<int:member_id>/status/<string:new_status>', methods=['POST'])
@login_required
@librarian_required
def change_status(member_id: int, new_status: str):
    member = Member.query.get_or_404(member_id)
    try:
        member.status = MemberStatus[new_status.upper()]
    except KeyError:
        abort(400)
    db.session.commit()
    flash(f'Member status changed to {member.status.value.title()}.', 'success')
    return redirect(url_for('members.member_detail', member_id=member.id))
