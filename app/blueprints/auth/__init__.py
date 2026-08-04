from flask import Blueprint, current_app, flash, redirect, render_template, url_for
from flask_login import current_user, login_user, logout_user

from app.forms import LoginForm

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        user_store = current_app.extensions["user_store"]
        user = user_store.authenticate(form.username.data, form.password.data)
        if user is not None:
            login_user(user)
            return redirect(url_for("dashboard.dashboard"))
        flash("Invalid username or password", "error")

    return render_template("auth/login.html", form=form)


@auth_bp.post("/logout")
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
