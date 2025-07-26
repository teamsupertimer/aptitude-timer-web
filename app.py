#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A simple Flask application that provides a timer utility for popular
Korean corporate aptitude tests such as Samsung's GSAT, SK Group's
SKCT and Hyundai's HMAT.  Users can register for an account, log in
and have their custom timer preferences saved to a local SQLite
database.  Pre‑configured durations for each exam are based on
published sources so candidates can practise under realistic
conditions.【979659461643808†screenshot】【774279807464311†screenshot】【809860645510307†screenshot】【140599651556413†screenshot】.

To run the application you need Flask installed.  You can install
dependencies with:

    pip install flask

Then run the server from within this directory:

    python app.py

By default the server listens on http://127.0.0.1:5000/.
"""

import os
import sqlite3
from datetime import datetime

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    g,
)
from werkzeug.security import generate_password_hash, check_password_hash


DATABASE = os.path.join(os.path.dirname(__file__), "database.db")


def create_app():
    """Application factory used to create the Flask app."""
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY="change-me-please",  # should be overridden in production
        DATABASE=DATABASE,
    )

    def get_db():
        """Return a SQLite connection from the application context."""
        if "db" not in g:
            conn = sqlite3.connect(app.config["DATABASE"])
            conn.row_factory = sqlite3.Row
            g.db = conn
        return g.db

    @app.teardown_appcontext
    def close_db(exception):
        """Close the database at the end of the request."""
        db = g.pop("db", None)
        if db is not None:
            db.close()

    def init_db():
        """Initialise the database with required tables if they don't exist."""
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS timers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                exam_name TEXT NOT NULL,
                minutes INTEGER NOT NULL,
                created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );
        """
        )
        db.commit()

    # Make the DB initialiser available on the app so it can be
    # invoked from the CLI.
    app.init_db = init_db

    # Provide db function to templates
    app.get_db = get_db

    # Pre‑configured test durations (in minutes) derived from cited sources.
    PRESET_TIMERS = {
        "GSAT": 140,  # Samsung aptitude test: 160 questions in 140 minutes【979659461643808†screenshot】【140599651556413†screenshot】
        "SKCT": 150,  # SK competency test: execution/intelligence (90min) + deep capability (60min)【774279807464311†screenshot】
        "HMAT": 145,  # Hyundai aptitude test: section times sum to roughly 145min【809860645510307†screenshot】
    }

    def current_user():
        """Return the currently logged in user row or None."""
        user_id = session.get("user_id")
        if user_id is None:
            return None
        db = get_db()
        cur = db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        return cur.fetchone()

    @app.context_processor
    def inject_globals():
        """Inject common variables into templates."""
        return {
            "current_user": current_user(),
            "PRESET_TIMERS": PRESET_TIMERS,
        }

    @app.route("/")
    def index():
        """Landing page. Redirect to dashboard if logged in, else to login."""
        if current_user():
            return redirect(url_for("dashboard"))
        return redirect(url_for("login"))

    @app.route("/register", methods=["GET", "POST"])
    def register():
        """Handle user registration."""
        if current_user():
            return redirect(url_for("dashboard"))
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "").strip()
            password2 = request.form.get("password2", "").strip()
            if not username or not password:
                flash("아이디와 비밀번호를 모두 입력해주세요.")
                return render_template("register.html")
            if password != password2:
                flash("비밀번호가 일치하지 않습니다.")
                return render_template("register.html")
            db = get_db()
            # Check duplicate
            existing = db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
            if existing:
                flash("이미 존재하는 아이디입니다.")
                return render_template("register.html")
            hashed = generate_password_hash(password)
            db.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed))
            db.commit()
            flash("회원가입이 완료되었습니다. 로그인해주세요.")
            return redirect(url_for("login"))
        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        """Handle user login."""
        if current_user():
            return redirect(url_for("dashboard"))
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            db = get_db()
            user = db.execute(
                "SELECT * FROM users WHERE username = ?", (username,)
            ).fetchone()
            if user and check_password_hash(user["password"], password):
                session["user_id"] = user["id"]
                flash("로그인 되었습니다.")
                return redirect(url_for("dashboard"))
            flash("아이디 혹은 비밀번호가 올바르지 않습니다.")
        return render_template("login.html")

    @app.route("/logout")
    def logout():
        """Log the user out and clear the session."""
        session.pop("user_id", None)
        flash("로그아웃되었습니다.")
        return redirect(url_for("login"))

    @app.route("/dashboard", methods=["GET", "POST"])
    def dashboard():
        """Show a dashboard with preset timers and saved custom timers."""
        user = current_user()
        if not user:
            return redirect(url_for("login"))
        db = get_db()
        # Handle adding a custom timer
        if request.method == "POST":
            exam_name = request.form.get("exam_name", "사용자 정의").strip() or "사용자 정의"
            minutes = request.form.get("minutes", "").strip()
            try:
                minutes_int = int(minutes)
                if minutes_int <= 0:
                    raise ValueError
            except ValueError:
                flash("시간을 올바르게 입력해주세요 (분 단위 양의 정수).")
            else:
                db.execute(
                    "INSERT INTO timers (user_id, exam_name, minutes) VALUES (?, ?, ?)",
                    (user["id"], exam_name, minutes_int),
                )
                db.commit()
                flash("사용자 정의 타이머가 저장되었습니다.")
                return redirect(url_for("dashboard"))
        # Query saved timers
        timers = db.execute(
            "SELECT * FROM timers WHERE user_id = ? ORDER BY created DESC", (user["id"],)
        ).fetchall()
        return render_template("dashboard.html", timers=timers)

    @app.route("/timer/<exam>")
    def timer(exam):
        """Render a timer page for a given exam or saved timer id."""
        user = current_user()
        if not user:
            return redirect(url_for("login"))
        db = get_db()
        # If exam corresponds to a saved timer id (numeric), fetch it
        minutes = None
        name = None
        if exam.isdigit():
            row = db.execute(
                "SELECT exam_name, minutes FROM timers WHERE id = ? AND user_id = ?",
                (int(exam), user["id"]),
            ).fetchone()
            if not row:
                flash("해당 타이머를 찾을 수 없습니다.")
                return redirect(url_for("dashboard"))
            name = row["exam_name"]
            minutes = row["minutes"]
        else:
            # Predefined exam name
            name = exam
            minutes = PRESET_TIMERS.get(exam)
            if minutes is None:
                flash("알 수 없는 시험입니다.")
                return redirect(url_for("dashboard"))
        return render_template("timer.html", exam_name=name, minutes=minutes)

    return app


if __name__ == "__main__":
    # Create the application and initialise the database if necessary
    app = create_app()
    if not os.path.exists(app.config["DATABASE"]):
        with app.app_context():
            app.init_db()
    # Run the development server
    app.run(debug=True)