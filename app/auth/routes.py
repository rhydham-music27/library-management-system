from urllib.parse import urlparse

from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required

from app.auth import bp
from app.extensions import db
from app.models import User, UserRole
from .forms import LoginForm, RegisterForm, ProfileForm, ChangePasswordForm


def _safe_redirect_target(next_url: str, default: str):
    if next_url and urlparse(next_url).netloc == "":
        return next_url
    return default


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data) and user.is_active:
            login_user(user, remember=form.remember_me.data)
            flash("Signed in successfully.", "success")
            next_url = request.args.get("next")
            return redirect(_safe_redirect_target(next_url, url_for("main.index")))
        flash("Invalid username or password, or account disabled.", "danger")
    return render_template("auth/login.html", form=form)


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been signed out.", "success")
    return redirect(url_for("main.index"))


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data,
            role=UserRole.MEMBER,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Registration successful. You can now sign in.", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/register.html", form=form)


@bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = ProfileForm()
    if form.validate_on_submit():
        current_user.full_name = form.full_name.data
        current_user.email = form.email.data
        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("auth.profile"))

    if request.method == "GET":
        form.full_name.data = current_user.full_name
        form.email.data = current_user.email
    return render_template("auth/profile.html", form=form, user=current_user)


@bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash("Current password is incorrect.", "danger")
        else:
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash("Password changed successfully.", "success")
            return redirect(url_for("auth.profile"))
    return render_template("auth/change_password.html", form=form)
