from flask import Blueprint, render_template, request, redirect, url_for, flash

auth = Blueprint('auth', __name__)

@auth.route("/login")
def login():
    return render_template("auth/login.html")


@auth.route("/register")
def register():
    return render_template("auth/register.html")


# 🔐 NUEVA RUTA
@auth.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":
        email = request.form.get("email")

        #  VALIDACIÓN
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
        confirm = request.form.get("confirm_password")

        if password != confirm:
            flash("Passwords do not match", "error")
            return redirect(request.url)

        # 🔥 AQUÍ IRÁ LUEGO LA BD
        print(f"[RESET PASSWORD] New password: {password}")

        # ✅ MENSAJE DE ÉXITO
        flash("Password updated successfully", "success")

        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", token=token)