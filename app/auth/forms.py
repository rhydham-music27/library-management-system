from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, EmailField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from flask_login import current_user

from app.models import User


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember me")
    submit = SubmitField("Sign In")


class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=80)])
    email = EmailField("Email", validators=[DataRequired(), Email()])
    full_name = StringField("Full name", validators=[DataRequired(), Length(max=100)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8)])
    password2 = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password", message="Passwords must match")]
    )
    submit = SubmitField("Register")

    def validate_username(self, username):
        if User.query.filter_by(username=username.data).first():
            raise ValidationError("This username is already taken.")

    def validate_email(self, email):
        if User.query.filter_by(email=email.data).first():
            raise ValidationError("This email is already registered.")


class ProfileForm(FlaskForm):
    full_name = StringField("Full name", validators=[DataRequired(), Length(max=100)])
    email = EmailField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Update Profile")

    def validate_email(self, email):
        existing = User.query.filter_by(email=email.data).first()
        if existing and (not current_user.is_authenticated or existing.id != current_user.id):
            raise ValidationError("This email is already in use by another account.")


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField("Current Password", validators=[DataRequired()])
    new_password = PasswordField("New Password", validators=[DataRequired(), Length(min=8)])
    new_password2 = PasswordField(
        "Confirm New Password", validators=[DataRequired(), EqualTo("new_password")]
    )
    submit = SubmitField("Change Password")
