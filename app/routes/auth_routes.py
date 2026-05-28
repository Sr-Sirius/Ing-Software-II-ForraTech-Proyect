from flask import Blueprint, render_template, request, redirect, url_for, flash

auth = Blueprint('auth', __name__)

@auth.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        flash("Login successful", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("auth/login.html")


@auth.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        # luego aquí irá lógica real
        flash("Account created successfully", "success")

        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@auth.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":
        email = request.form.get("email")

        if not email:
            flash("Email is required", "error")
            return redirect(request.url)

        print(f"[FORGOT PASSWORD] Email received: {email}")

        flash("If the email exists, a reset link was sent.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/forgot_password.html")


@auth.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):

    if request.method == "POST":
        password = request.form.get("password")
        confirm = request.form.get("confirm-password")  # ✅ FIX

        if not password or not confirm:
            flash("All fields are required", "error")
            return redirect(request.url)

        if len(password) < 6:
            flash("Password must be at least 6 characters", "error")
            return redirect(request.url)

        if password != confirm:
            flash("Passwords do not match", "error")
            return redirect(request.url)

        print(f"[RESET PASSWORD] New password: {password}")

        flash("Password updated successfully", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", token=token)