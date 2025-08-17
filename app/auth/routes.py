from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from .forms import RegisterForm, LoginForm, ProfileForm
from .user_model import get_user_by_email, get_user_by_id, get_user_by_username, User
from db.core import execute, query_one

auth_bp = Blueprint("auth", __name__, url_prefix="/auth", template_folder="templates")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = get_user_by_email(form.email.data)
        if not user:
            flash("Invalid credentials.", "error")
            return render_template("auth/login.html", form=form)

        row = query_one("SELECT password_hash FROM users WHERE id = ?", (user.id,))
        if row and check_password_hash(row["password_hash"], form.password.data):
            login_user(user, remember=True)
            flash("Logged in.", "success")
            next_url = request.args.get("next") or url_for("dashboard.index")
            return redirect(next_url)
        flash("Invalid credentials.", "error")

    return render_template("auth/login.html", form=form)

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out.", "info")
    return redirect(url_for("auth.login"))

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if get_user_by_email(form.email.data):
            flash("Email already registered.", "error")
            return render_template("auth/register.html", form=form)
        if get_user_by_username(form.username.data):
            flash("Username already taken.", "error")
            return render_template("auth/register.html", form=form)
        
        password_hash = generate_password_hash(form.password.data)

        try:
            user_id = execute(
                """
                INSERT INTO users (username, email, password_hash)
                VALUES (?, ?, ?)
                """,
                (form.username.data, form.email.data, password_hash),
            )
        except Exception as e:
            flash("Registration failed. Please try a different email/username.", "error")
            return render_template("auth/register.html", form=form)

        row = query_one(
            """
            SELECT * FROM users WHERE id = ?
            """, 
            (user_id,)
        )
        user = User.from_row(row)
        login_user(user)
        flash("Welcome! Account created.", "success")
        return redirect(url_for("dashboard.index"))
    
    return render_template("auth/register.html", form=form)

@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    row = query_one("SELECT electricity_rate FROM users WHERE id = ?", (current_user.id,))
    current_rate = row["electricity_rate"] if row else 0.0
    form = ProfileForm(electricity_rate=current_rate)

    if form.validate_on_submit():
        execute(
            "UPDATE users SET electricity_rate = ? WHERE id = ?",
            (form.electricity_rate.data, current_user.id),
        )
        updated_row = query_one("SELECT * FROM users WHERE id = ?", (current_user.id,))
        refreshed = User.from_row(updated_row)
        current_user.electricity_rate = refreshed.electricity_rate

        flash("Profile updated.", "success")
        return redirect(url_for("auth.profile"))

    return render_template("auth/profile.html", form=form, rate=current_rate)