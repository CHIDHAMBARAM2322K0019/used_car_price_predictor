from flask import Flask, request, render_template, redirect, url_for, session
import numpy as np
import pickle as pk
import sqlite3
from werkzeug.security import check_password_hash, generate_password_hash
from flask import jsonify

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
    return render_template("index.html", role=session["role"]
                           ,username=session["user"])


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
    return render_template("admin.html")

# 👤 User Dashboard
@app.route("/user_dashboard")
def user_dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    cur = conn.cursor()

    # current user oda total predictions
    cur.execute(
        "SELECT COUNT(*) FROM predictions WHERE username=?",
        (session["user"],)
    )
    user_predictions = cur.fetchone()[0]

    conn.close()

    return render_template(
        "user_dashboard.html",
        username=session["user"],
        user_predictions=user_predictions
    )

# ChatBot module
@app.route("/chat", methods=["POST"])
def chat():
    if "user" not in session:
        return jsonify({"reply": "Please log in to continue."})

    user_msg = request.json.get("message", "").lower()

    if "hi" in user_msg or "hello" in user_msg:
        reply = "Hello. How may I assist you with used car details today?"

    elif "price" in user_msg:
        reply = "Please provide the car brand, manufacturing year, fuel type, and kilometers driven to receive a price prediction."

    elif "diesel" in user_msg:
        reply = "Diesel vehicles are generally suitable for long-distance travel and offer better fuel efficiency for extended usage."

    elif "petrol" in user_msg:
        reply = "Petrol vehicles are ideal for city driving and typically provide a smoother and quieter experience."

    elif "mileage" in user_msg:
        reply = "Please enter the vehicle’s mileage efficiency in kilometers per liter (km/l)."

    elif "power" in user_msg or "max power" in user_msg:
        reply = "Please enter the maximum power output of the vehicle as specified by the manufacturer (e.g., 82 bhp)."

    elif "seat" in user_msg:
        reply = "Please enter the total seating capacity of the vehicle (e.g., 5)."

    elif "fuel" in user_msg or "petrol" in user_msg or "diesel" in user_msg:
        reply = "Please select the fuel type of the vehicle (Petrol or Diesel)."

    elif "seller type" in user_msg or "seller" in user_msg:
        reply = "Please specify the seller type (Individual or Dealer)."

    elif "transmission" in user_msg:
        reply = "Please select the transmission type (Manual or Automatic)."

    elif "owner" in user_msg:
        reply = "Please select the number of previous owners (e.g.,First Owner , Second owner)."
     
    elif "help" in user_msg:
        reply = "Kindly complete the form and click the 'Predict' button to proceed."

    elif "engine" in user_msg:
        reply = "Please enter the engine capacity in cubic centimeters (CC) (e.g., 1197)."
 
    elif "year" in user_msg or "manufacture" in user_msg:
        reply = "Please enter the vehicle's manufacturing year in four-digit format (e.g., 2018)." 
    
    elif "km driven" in user_msg or "kilometer" in user_msg or "driven" in user_msg:
        reply = "Please enter the total distance the vehicle has been driven in kilometers (e.g., 45000)."

    else:
        reply = "I'm sorry, I did not understand your request. Please provide more specific details."

    return jsonify({"reply": reply})

# Analytics
@app.route("/analytics")
def analytics():
    if "user" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM users WHERE role='admin'")
    admin_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM users WHERE role='user'")
    user_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM predictions")
    total_predictions = cur.fetchone()[0]

    conn.close()

    return render_template(
        "analytics.html",
        total_users=total_users,
        admin_count=admin_count,
        user_count=user_count,
        total_predictions=total_predictions
    )

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

        # Save prediction count for analytics
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
    """INSERT INTO predictions 
    (username, year, km_driven, fuel, brand, predicted_price) 
    VALUES (?, ?, ?, ?, ?, ?)""",
    (session["user"], year, km_driven, fuel, name, prediction)
)

        conn.commit()
        conn.close()

        return render_template(
            "index.html",
            role=session["role"],
            username=session["user"],
            prediction_text=f"Estimated Car Price: ₹ {prediction:,}"
        )

    except Exception as e:
        print("ERROR:", e)
        return render_template(
            "index.html",
            role=session["role"],
            username=session["user"],
            prediction_text="⚠️ Please fill all fields correctly"
        )


# 🚪 Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/history")
def history():

    if "user" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute("SELECT brand ,year, km_driven, fuel, predicted_price, created_at FROM predictions WHERE username=?", (session["user"],))

    data = cursor.fetchall()

    conn.close()

    return render_template("history.html", predictions=data)


if __name__ == "__main__":
    app.run(debug=True)



