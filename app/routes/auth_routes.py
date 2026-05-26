from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer

from app.db import get_connection
from app import mail

auth = Blueprint("auth", __name__)

# =========================
# SERIALIZER
# =========================

serializer = URLSafeTimedSerializer("supersecretkey")

# =========================
# LOGIN
# =========================

@auth.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, fullname, username, email, password
            FROM users
            WHERE email = %s OR username = %s
        """, (email, email))

        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user and check_password_hash(user[4], password):

            flash(f"Welcome {user[1]}!", "success")

            return redirect(url_for("main.home"))

        flash("Invalid credentials", "error")

    return render_template("auth/login.html")

# =========================
# REGISTER
# =========================

@auth.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        fullname = request.form.get("fullname")
        email = request.form.get("email")
        username = request.form.get("username")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        user_type = request.form.get("user_type")
        phone = request.form.get("phone")
        location = request.form.get("location")

        # VALIDAR PASSWORDS

        if password != confirm_password:

            flash("Passwords do not match", "error")

            return redirect(request.url)

        hashed_password = generate_password_hash(password)

        conn = get_connection()
        cursor = conn.cursor()

        # VERIFICAR EXISTENTE

        cursor.execute("""
            SELECT *
            FROM users
            WHERE email = %s OR username = %s
        """, (email, username))

        existing_user = cursor.fetchone()

        if existing_user:

            flash("Email or username already exists", "error")

            cursor.close()
            conn.close()

            return redirect(request.url)

        # INSERTAR USUARIO

        cursor.execute("""
            INSERT INTO users (

                fullname,
                username,
                email,
                password,
                user_type,
                phone,
                location

            )

            VALUES (%s, %s, %s, %s, %s, %s, %s)

        """, (

            fullname,
            username,
            email,
            hashed_password,
            user_type,
            phone,
            location

        ))

        conn.commit()

        cursor.close()
        conn.close()

        flash("Account created successfully", "success")

        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")

# =========================
# FORGOT PASSWORD
# =========================

@auth.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":

        email = request.form.get("email")

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM users
            WHERE email = %s
        """, (email,))

        user = cursor.fetchone()

        cursor.close()
        conn.close()

        # SI EXISTE

        if user:

            # TOKEN

            token = serializer.dumps(
                email,
                salt="reset-password"
            )

            # LINK

            reset_link = url_for(

                "auth.reset_password",

                token=token,

                _external=True
            )

            # EMAIL

            msg = Message(

                subject="Reset Your Password",

                sender="TU_CORREO@gmail.com",

                recipients=[email]
            )

            msg.body = f"""
Hello,

Click the link below to reset your password:

{reset_link}

If you did not request this, ignore this email.
"""

            mail.send(msg)

        flash(
            "If the email exists, a reset link was sent.",
            "success"
        )

        return redirect(url_for("auth.login"))

    return render_template("auth/forgot_password.html")

# =========================
# RESET PASSWORD
# =========================

@auth.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):

    try:

        email = serializer.loads(

            token,

            salt="reset-password",

            max_age=3600
        )

    except:

        flash("Invalid or expired token", "error")

        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":

        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if password != confirm_password:

            flash("Passwords do not match", "error")

            return redirect(request.url)

        hashed_password = generate_password_hash(password)

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE users
            SET password = %s
            WHERE email = %s
        """, (

            hashed_password,
            email
        ))

        conn.commit()

        cursor.close()
        conn.close()

        flash("Password updated successfully", "success")

        return redirect(url_for("auth.login"))

    return render_template(
        "auth/reset_password.html",
        token=token
    )