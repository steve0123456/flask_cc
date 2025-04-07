from flask import Flask, render_template, request, redirect, session, url_for, jsonify
import firebase_admin
from firebase_admin import auth, credentials, firestore
import os
import pandas as pd

import config
# Initialize Firebase Admin SDK if not already initialized
if not firebase_admin._apps:
    cred = credentials.Certificate("path/to/your/firebase-adminsdk.json")  # Update with actual path
    firebase_admin.initialize_app(cred)

# Initialize Firestore
db = firebase_admin.firestore.client()

app = Flask(__name__)
app.secret_key = "your-secret-key"  # Replace with a strong secret key

@app.route("/")
def home():
    if "user" in session:
        return render_template("home.html", user=session["user"])
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        try:
            user = auth.get_user_by_email(email)  # Check if user exists
            session["user"] = {"uid": user.uid, "email": user.email}
            return redirect(url_for("home"))
        except Exception as e:
            return jsonify({"error": str(e)}), 400
    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        try:
            user = auth.create_user(email=email, password=password)
            session["user"] = {"uid": user.uid, "email": user.email}
            return redirect(url_for("home"))
        except Exception as e:
            return jsonify({"error": str(e)}), 400
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))


budget = {"amount": 0}
expenses = []
condition_budget = ""
condition_expenses = ""
condition_earners = 0
state = ""
overall = ""


@app.route("/expense", methods=["GET", "POST"])
def expense():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        if "new_budget" in request.form:
            # Update budget
            new_budget = request.form.get("new_budget")
            if new_budget.isdigit():
                budget["amount"] = int(new_budget)

        elif "expense_title" in request.form:
            # Add new expense
            title = request.form.get("expense_title")
            amount = request.form.get("expense_amount")
            date = request.form.get("expense_date")

            if title and amount.isdigit() and date:
                expenses.append({
                    "title": title,
                    "amount": int(amount),
                    "date": date
                })

        elif "delete_index" in request.form:
            # Delete expense by index
            index = int(request.form.get("delete_index"))
            if 0 <= index < len(expenses):
                expenses.pop(index)

    return render_template("expense.html", budget=budget["amount"], expenses=expenses)


@app.route("/analytics", methods=["GET"])
def analytics():
    df = pd.read_csv("Inc_Exp_Data.csv")

    first_column = df.iloc[:, 0]
    second_column = df.iloc[:, 1]

    min_budget1 = first_column.min()
    avg_budget1 = first_column.mean()
    max_budget1 = first_column.max()

    min_budget2 = second_column.min()
    avg_budget2 = second_column.mean()
    max_budget2 = second_column.max()

    # Use budget['amount'] correctly
    if budget["amount"] + 2500 < min_budget1:
        condition_budget = "Low"
    elif budget["amount"] - 2500 > max_budget1 or budget["amount"] == max_budget1:
        condition_budget = "High"
    else:
        condition_budget = "Medium"

    # Calculate total expense
    total_expense = sum(e["amount"] for e in expenses)

    if total_expense + 1000 > max_budget2:
        condition_expenses = "Low"
    elif total_expense + 2000 < min_budget2 or total_expense == min_budget2:
        condition_expenses = "High"
    else:
        condition_expenses = "Medium"

    # Dummy logic for condition_earners — you may update this
    if condition_earners == 1:
        state = "High"
    else:
        state = "Low"

    if condition_budget == "Low" and (condition_expenses == "Low" or condition_expenses == "Medium"):
        overall = "Low"
    elif condition_budget == "High" and (condition_expenses == "High" or condition_expenses == "Low"):
        overall = "High"
    else:
        overall = "Medium"

    return render_template(
        "analytics.html",
        overall=overall,
        condition_budget=condition_budget,
        condition_expenses=condition_expenses,
        state=state
    )



# ✅ Show Profile Page
"""
@app.route("/profile", methods=["GET"])
def profile():
    if "user" not in session:
        return redirect(url_for("login"))

    return render_template("profile.html")

"""

# ✅ Save Profile Data to Firestore
@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "user" not in session:
        return redirect(url_for("login"))

    user_email = session["user"]["email"]
    profile_ref = db.collection("user-data").document(user_email)

    if request.method == "POST":
        # Save or update profile data
        name = request.form.get("name")
        age = request.form.get("age")
        place = request.form.get("place")
        income = request.form.get("income")

        if not all([name, age, place, income]):
            return jsonify({"error": "All fields are required"}), 400

        profile_ref.set({
            "name": name,
            "age": int(age),
            "place": place,
            "income": int(income)
        })

        return redirect(url_for("home"))

    else:
        # GET request: fetch existing data if any
        profile_doc = profile_ref.get()
        profile_data = profile_doc.to_dict() if profile_doc.exists else {}

        return render_template("profile.html", profile=profile_data)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
