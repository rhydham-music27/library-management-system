from datetime import date, timedelta

from flask_wtf import FlaskForm
from wtforms import DateField, SelectField, SubmitField
from wtforms.validators import DataRequired, Optional, ValidationError


class DateRangeForm(FlaskForm):
    start_date = DateField('Start Date', format='%Y-%m-%d', validators=[Optional()], default=lambda: date.today() - timedelta(days=30))
    end_date = DateField('End Date', format='%Y-%m-%d', validators=[Optional()], default=lambda: date.today())
    submit = SubmitField('Apply Filter')

    def validate_end_date(self, end_date):
        s = self.start_date.data
        e = end_date.data
        if s and e:
            if e < s:
                raise ValidationError('End date must be after start date.')
            if e > date.today():
                raise ValidationError('End date cannot be in the future.')


class ReportTypeForm(FlaskForm):
    report_type = SelectField(
        'Report Type',
        validators=[DataRequired()],
        coerce=str,
        choices=[
            ('most_borrowed', 'Most Borrowed Books'),
            ('active_members', 'Active Members'),
            ('overdue_summary', 'Overdue Summary'),
            ('collection_stats', 'Collection Statistics'),
            ('circulation_trends', 'Circulation Trends'),
        ],
    )
    date_range = SelectField(
        'Date Range',
        validators=[Optional()],
        coerce=str,
        default='30',
        choices=[
            ('7', 'Last 7 Days'),
            ('30', 'Last 30 Days'),
            ('90', 'Last 90 Days'),
            ('365', 'Last Year'),
            ('all', 'All Time'),
            ('custom', 'Custom Range'),
        ],
    )
    submit = SubmitField('Generate Report')
