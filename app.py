"""
Flask API — AI Financial Intelligence Engine
=============================================================
"""

import os
import time
import logging
import pandas as pd
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template, send_from_directory
import uuid
from flask_cors import CORS
import bcrypt
import jwt
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from financial_analyzer import (
    analyze_financial_behavior,
    spending_analysis,
    trend_analysis,
    financial_personality,
    spending_prediction,
    financial_health_score,
    insight_engine,
    recommendation_engine,
    whatif_simulation,
)

from config import settings
from database import SessionLocal, init_db, TransactionAudit, UserProfile, User, Transaction

import numpy as np
from model import predict as ml_predict, get_model, get_model_info


# ─── Config ──────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-28s | %(levelname)-7s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("app")

CSV_PATH = os.path.join(os.path.dirname(__file__), "data.csv")

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)
app.config["SECRET_KEY"] = settings.secret_key

# ─── Helpers ─────────────────────────────────────────────────────────────────────

def get_current_user():
    token = request.cookies.get("auth_token")
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
        return payload.get("user_id")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def get_user_df(user_id):
    db = SessionLocal()
    try:
        txns = db.query(Transaction).filter(Transaction.user_id == user_id).all()
        if not txns:
            return pd.DataFrame(columns=["date", "amount", "category"])
        
        data = [{"date": t.date, "amount": t.amount, "category": t.category} for t in txns]
        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
        return df
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════════════
# FINANCIAL ANALYZER ROUTES
# ═══════════════════════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/transactions", methods=["GET"])
def get_transactions():
    user_id = get_current_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    df = get_user_df(user_id)
    return jsonify({
        "transactions": df.to_dict(orient="records"),
        "count": len(df),
    })


@app.route("/api/add_transaction", methods=["POST"])
def add_transaction():
    user_id = get_current_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "No JSON body"}), 400

    date = data.get("date")
    amount = data.get("amount")
    category = data.get("category")

    if not all([date, amount, category]):
        return jsonify({"error": "date, amount, and category are required"}), 400

    try:
        amount = float(amount)
    except (ValueError, TypeError):
        return jsonify({"error": "amount must be a number"}), 400

    valid_cats = ["Food", "Transport", "Shopping", "Bills", "Entertainment", "Others"]
    if category not in valid_cats:
        return jsonify({"error": f"category must be one of: {valid_cats}"}), 400

    db = SessionLocal()
    try:
        new_txn = Transaction(user_id=user_id, date=date, amount=amount, category=category)
        db.add(new_txn)
        
        user = db.query(User).filter(User.user_id == user_id).first()
        salary = user.monthly_income if user else 0
        db.commit()
    finally:
        db.close()
        
    df = get_user_df(user_id)

    analysis = None
    if salary > 0:
        analysis = analyze_financial_behavior(df, salary)

    return jsonify({
        "success": True,
        "transaction": {"date": date, "amount": amount, "category": category},
        "analysis": analysis,
    })


@app.route("/api/analysis", methods=["GET"])
def get_analysis():
    user_id = get_current_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    df = get_user_df(user_id)
    if len(df) == 0:
        return jsonify({"error": "No transactions found. Add some first."}), 404
        
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        salary = user.monthly_income if user else 0
    finally:
        db.close()
        
    if salary <= 0:
        return jsonify({"error": "Configuration required. Please configure your monthly salary."}), 400
        
    analysis = analyze_financial_behavior(df, salary)
    return jsonify(analysis)


@app.route("/api/whatif", methods=["POST"])
def whatif():
    user_id = get_current_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "No JSON body"}), 400

    category = data.get("category")
    percent = data.get("percent", 0)

    df = get_user_df(user_id)
    if len(df) == 0:
        return jsonify({"error": "No transactions"}), 404
        
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        salary = user.monthly_income if user else 0
    finally:
        db.close()
        
    if salary <= 0:
        return jsonify({"error": "Configuration required. Please configure your monthly salary."}), 400

    result = whatif_simulation(df, salary, category, percent)
    return jsonify(result)


@app.route("/api/user/salary", methods=["GET", "POST"])
def user_salary():
    user_id = get_current_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
            
        if request.method == "POST":
            data = request.get_json(silent=True) or {}
            salary = data.get("salary")
            try:
                salary = float(salary)
                if salary <= 0:
                    raise ValueError()
            except (ValueError, TypeError):
                return jsonify({"error": "Valid positive salary is required"}), 400
            
            user.monthly_income = salary
            db.commit()
            return jsonify({"success": True, "salary": salary})
        
        return jsonify({"salary": user.monthly_income})
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════════════
# AUTHENTICATION ROUTES
# ═══════════════════════════════════════════════════════════════════════════════════

import uuid

def create_jwt(user_id):
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(seconds=settings.jwt_access_token_expires)
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")


@app.route("/api/auth/signup", methods=["POST"])
def auth_signup():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False, "error": "No JSON body"}), 400

    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not name or not email or len(password) < 6:
        return jsonify({"success": False, "error": "Name, email, and password (min 6 chars) required"}), 400

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            return jsonify({"success": False, "error": "Email already registered. Try logging in."}), 400

        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user_id = "usr_" + uuid.uuid4().hex[:12]
        
        new_user = User(
            user_id=user_id,
            name=name,
            email=email,
            password_hash=hashed,
            monthly_income=0
        )
        db.add(new_user)
        db.commit()
        
        token = create_jwt(user_id)
        
        response = jsonify({"success": True, "user": {"name": name, "email": email}})
        response.set_cookie("auth_token", token, httponly=True, secure=False, samesite='Lax', max_age=settings.jwt_access_token_expires)
        logger.info(f"New user registered: {email}")
        return response
    finally:
        db.close()


@app.route("/api/auth/login", methods=["POST"])
def auth_login():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False, "error": "No JSON body"}), 400

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user or not user.password_hash:
            return jsonify({"success": False, "error": "Invalid email or password"}), 401

        if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            return jsonify({"success": False, "error": "Invalid email or password"}), 401

        token = create_jwt(user.user_id)
        
        response = jsonify({"success": True, "user": {"name": user.name, "email": email}})
        response.set_cookie("auth_token", token, httponly=True, secure=False, samesite='Lax', max_age=settings.jwt_access_token_expires)
        logger.info(f"User logged in: {email}")
        return response
    finally:
        db.close()


@app.route("/api/auth/google", methods=["POST"])
def auth_google():
    data = request.get_json(silent=True)
    token = data.get("token")
    if not token:
        return jsonify({"success": False, "error": "No token provided"}), 400
        
    try:
        idinfo = id_token.verify_oauth2_token(token, google_requests.Request(), settings.google_client_id, clock_skew_in_seconds=10)
        email = idinfo['email']
        name = idinfo.get('name', 'Google User')
        google_id = idinfo['sub']
        picture = idinfo.get('picture', '')
        
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.email == email).first()
            if not user:
                user_id = "usr_" + uuid.uuid4().hex[:12]
                user = User(
                    user_id=user_id,
                    name=name,
                    email=email,
                    google_id=google_id,
                    profile_image=picture,
                    monthly_income=0
                )
                db.add(user)
                db.commit()
            elif not user.google_id:
                user.google_id = google_id
                if not user.profile_image:
                    user.profile_image = picture
                db.commit()
                
            jwt_token = create_jwt(user.user_id)
            response = jsonify({"success": True, "user": {"name": user.name, "email": email, "picture": picture}})
            response.set_cookie("auth_token", jwt_token, httponly=True, secure=False, samesite='Lax', max_age=settings.jwt_access_token_expires)
            return response
        finally:
            db.close()
            
    except ValueError as e:
        logger.error(f"Google Token Verification Error: {e}")
        return jsonify({"success": False, "error": "Invalid Google token"}), 401


@app.route("/api/auth/logout", methods=["POST"])
def auth_logout():
    response = jsonify({"success": True})
    response.set_cookie("auth_token", "", expires=0)
    return response


@app.route("/api/auth/status", methods=["GET"])
def auth_status():
    user_id = get_current_user()
    if not user_id:
        return jsonify({"authenticated": False})
        
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if user:
            return jsonify({"authenticated": True, "user": {"name": user.name, "email": user.email}})
        return jsonify({"authenticated": False})
    finally:
        db.close()

@app.route("/api/user/settings", methods=["POST"])
def user_settings():
    user_id = get_current_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json(silent=True) or {}
    name = data.get("name")
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
             return jsonify({"error": "User not found"}), 404
             
        if name:
             user.name = name
             
        db.commit()
        return jsonify({"success": True, "user": {"name": user.name, "email": user.email}})
    finally:
        db.close()

@app.route("/api/user/password", methods=["POST"])
def change_password():
    user_id = get_current_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
        
    data = request.get_json(silent=True) or {}
    old_password = data.get("oldPassword", "")
    new_password = data.get("newPassword", "")
    
    if len(new_password) < 6:
        return jsonify({"error": "New password must be at least 6 characters"}), 400
        
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
            
        if user.password_hash:
            if not bcrypt.checkpw(old_password.encode('utf-8'), user.password_hash.encode('utf-8')):
                return jsonify({"error": "Incorrect old password"}), 401
                
        user.password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        db.commit()
        return jsonify({"success": True, "message": "Password updated successfully"})
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════════════
# SMART FINANCIAL DECISION ENGINE
# ═══════════════════════════════════════════════════════════════════════════════════

@app.route("/api/check_affordability", methods=["POST"])
def check_affordability():
    user_id = get_current_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "No JSON body"}), 400

    amount = data.get("amount")
    category = data.get("category")

    try:
        amount = float(amount)
        if amount <= 0:
            raise ValueError()
    except (ValueError, TypeError):
        return jsonify({"error": "Valid amount required"}), 400

    if not category:
        return jsonify({"error": "Category required"}), 400

    # Determine necessity
    essential_cats = ["Food", "Transport", "Bills"]
    necessity = "Essential" if category in essential_cats else "Optional"

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        salary = user.monthly_income if user else 0
    finally:
        db.close()

    if salary <= 0:
         return jsonify({"error": "Please set your monthly income in settings first."}), 400

    df = get_user_df(user_id)
    
    # Calculate ML features for our Isolation Forest
    mean_amount = float(df["amount"].mean()) if len(df) > 0 else amount
    amount_deviation = abs(amount - mean_amount) / mean_amount if mean_amount > 0 else 0
    
    # Simulate the 9 features format expected by model.py
    # Features: [login_deviation, amount_deviation, device_flag, location_flag, attempts, 
    #            transaction_velocity, time_since_last_transaction, daily_usage_ratio, transaction_frequency]
    features = [
        0, # login_deviation
        amount_deviation,
        0, # device_flag
        0, # location_flag
        1, # attempts
        0, # transaction_velocity
        120, # time_since_last_transaction
        (amount / salary) * 100, # daily_usage_ratio
        1, # transaction_frequency
    ]
    
    # Use existing Isolation Forest model to detect anomalous spending!
    features_array = np.array([features])
    ml_result = ml_predict(features_array)
    
    risk_score = float(ml_result.get("risk_score", 0))
    
    # Adjust risk score heuristically based on hard budget constraints
    total_spent = float(df["amount"].sum()) if len(df) > 0 else 0
    new_total = total_spent + amount
    budget_used_pct = (new_total / salary) * 100
    
    if budget_used_pct > 90:
        risk_score = max(risk_score, 95.0)
    elif budget_used_pct > 75:
        risk_score = max(risk_score, 75.0)
        
    if risk_score > 80:
        risk_level = "HIGH"
    elif risk_score > 50:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"
        
    # Generate insights dynamically
    if amount > mean_amount * 3:
        insight = f"This expense is 3x higher than your average transaction of ₹{mean_amount:,.0f}"
    elif risk_level == "HIGH":
        insight = "This expense significantly deviates from your safe spending patterns"
    else:
        insight = "This expense aligns perfectly with your normal spending pattern"
        
    impact = f"You will have used {budget_used_pct:.0f}% of your monthly budget (₹{salary:,.0f})"
    
    projected = (new_total / max(1, len(df.groupby('date')) if len(df)>0 else 1)) * 30
    if projected > salary:
        future_pred = "At this rate, your spending may exceed your budget by month's end"
    else:
        future_pred = f"You are on track to save ₹{(salary - projected):,.0f} this month"
        
    # Goal impact (assuming 20% savings goal)
    target_savings = salary * 0.2
    current_savings = salary - new_total
    if current_savings < target_savings:
        days_delayed = int(amount / max(1, (salary / 30)))
        goal_impact = f"This {necessity.lower()} expense may delay your savings goal by ~{days_delayed} days"
    else:
        goal_impact = "This expense keeps your savings goal safely on track"
        
    if necessity == "Essential" and current_savings >= target_savings:
        goal_impact = "Essential expenses are already safely factored into your budget"
        
    # Categories analysis
    cat_spent = float(df[df["category"] == category]["amount"].sum()) if len(df) > 0 else 0
    new_cat_spent = cat_spent + amount
    cat_pct = (new_cat_spent / new_total) * 100
    cat_analysis = f"{category} now accounts for {cat_pct:.0f}% of your total spending"
    
    if necessity == "Optional" and risk_level in ["MEDIUM", "HIGH"]:
        suggestion = "• Consider reducing optional expenses this week\n• Wait 48 hours before purchasing"
        opportunities = f"You can save ₹{amount:,.0f} directly by avoiding this discretionary expense"
    else:
        suggestion = "• Monitor your remaining budget progress\n• Ensure this is logged accurately"
        opportunities = "Consider using a cashback card or rewards program for this purchase"
         
    # Weekly trend
    if len(df) > 0:
        import datetime
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=7)
        try:
            df["date"] = pd.to_datetime(df["date"])
            last_7_days = (df["date"] >= start_date) & (df["date"] <= end_date)
            weekly_total = float(df[last_7_days]["amount"].sum()) + amount
            trend_pct = (amount / max(1, weekly_total)) * 100
        except:
            trend_pct = 0
    else:
        trend_pct = 0
    trend = f"This represents {trend_pct:.0f}% of your spending over the last 7 days"
    
    # Behavior insight (heuristic based on category frequency)
    cat_count = len(df[df["category"] == category]) if len(df) > 0 else 0
    if cat_count > len(df) * 0.4:
        behavior = f"You are heavily reliant on {category} purchases recently"
    else:
        behavior = "Your category spread remains balanced"
    
    if risk_level == "HIGH":
        affordability = "⚠️ High Risk: This will severely impact your savings and budget parameters."
    elif risk_level == "MEDIUM":
        affordability = "⚡ Caution: You can afford this, but it may delay your financial goals."
    else:
        affordability = "✅ Safe: This expense is well within your budget."

    return jsonify({
        "amount": amount,
        "category": category,
        "necessity": necessity,
        "risk_level": risk_level,
        "risk_score": round(risk_score, 1),
        "insight": insight,
        "impact": impact,
        "future_prediction": future_pred,
        "smart_suggestion": suggestion,
        "goal_impact": goal_impact,
        "category_analysis": cat_analysis,
        "weekly_trend": trend,
        "savings_opportunity": opportunities,
        "behavior_insight": behavior,
        "affordability_check": affordability
    })


# ═══════════════════════════════════════════════════════════════════════════════════
# START
# ═══════════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logger.info("Initializing database & ML model...")
    init_db()
    get_model()
    logger.info(f"Server starting on http://localhost:{settings.port}")
    app.run(host="0.0.0.0", port=settings.port, debug=settings.debug, threaded=True)
