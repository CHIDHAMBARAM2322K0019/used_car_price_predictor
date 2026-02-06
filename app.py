from flask import Flask, request, render_template, redirect, url_for, session
import numpy as np
import pickle as pk
import sqlite3
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = "used_car_price_prediction_secret"

# 🔮 ML model load
model = pk.load(open("model.pkl", "rb"))


# 🔗 DB connection helper
def get_db():
    return sqlite3.connect("users.db")


# 🏠 Home
@app.route("/")
def home():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("index.html", role=session["role"])


# 📝 Signup
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])
        role = "user"

        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                (username, password, role)
            )
            conn.commit()
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            return render_template("signup.html", error="⚠️ Username already exists")
        finally:
            conn.close()

    return render_template("signup.html")


# 🔐 Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT username, password, role FROM users WHERE username=?",
            (username,)
        )
        user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user[1], password):
            session["user"] = user[0]
            session["role"] = user[2]
            return redirect(url_for("home"))
        else:
            return render_template("login.html", error="❌ Invalid username or password")

    return render_template("login.html")


# 👑 Admin page
@app.route("/admin")
def admin():
    if "user" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))
    return "🔥 Welcome Admin"


# 🚗 Predict
@app.route("/predict", methods=["POST"])
def predict():
    if "user" not in session:
        return redirect(url_for("login"))

    try:
        name = int(request.form["name"])
        year = int(request.form["year"])
        km_driven = int(request.form["km_driven"])
        fuel = int(request.form["fuel"])
        seller_type = int(request.form["seller_type"])
        transmission = int(request.form["transmission"])
        owner = int(request.form["owner"])

        mileage = float(request.form["mileage"])
        engine = float(request.form["engine"])
        max_power = float(request.form["max_power"])
        seats = int(request.form["seats"])

        features = np.array([[name, year, km_driven, fuel,
                              seller_type, transmission, owner,
                              mileage, engine, max_power, seats]])

        prediction = max(0, int(model.predict(features)[0]))

        return render_template(
            "index.html",
            role=session["role"],
            prediction_text=f"Estimated Car Price: ₹ {prediction:,}"
        )

    except Exception as e:
        print("ERROR:", e)
        return render_template(
            "index.html",
            role=session["role"],
            prediction_text="⚠️ Please fill all fields correctly"
        )


# 🚪 Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)