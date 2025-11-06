from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Optional, Length, ValidationError

from app.models import Member, MemberStatus


class MemberForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    address = TextAreaField('Address', validators=[Optional()])
    status = SelectField(
        'Status',
        coerce=str,
        validators=[DataRequired()],
        choices=[(s.value, s.value.title()) for s in MemberStatus],
        default=MemberStatus.ACTIVE.value,
    )
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Save Member')

    def validate_email(self, email):
        existing = Member.query.filter_by(email=email.data).first()
        current = getattr(self, '_obj', None)
        if existing and (not current or existing.id != getattr(current, 'id', None)):
            raise ValidationError('This email is already registered.')


class MemberSearchForm(FlaskForm):
    query = StringField('Search', validators=[Optional()])
    status = SelectField(
        'Status',
        coerce=str,
        validators=[Optional()],
        choices=[('all', 'All Statuses')] + [(s.value, s.value.title()) for s in MemberStatus],
        default='all',
    )
    submit = SubmitField('Search')
