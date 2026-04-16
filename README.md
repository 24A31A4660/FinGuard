# FinGuard — Smart Financial Decision Engine 🧠💰

AI-powered financial intelligence platform that analyzes your spending patterns, evaluates purchase affordability in real-time using Machine Learning, and provides personalized financial insights.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.x-lightgrey?logo=flask)
![ML](https://img.shields.io/badge/ML-Isolation_Forest-green?logo=scikit-learn)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ Features

- **Smart Affordability Check** — ML-powered risk assessment for any purchase before you make it
- **8-Module Financial Analyzer** — Spending analysis, trend detection, personality profiling, health scoring, predictions, insights, recommendations, and what-if simulations
- **Real-Time Dashboard** — Interactive charts, category breakdowns, and payment history
- **Secure Authentication** — JWT-based login, Google OAuth 2.0, bcrypt password hashing
- **Data Isolation** — Complete separation between demo (landing page) and authenticated user data

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Flask, SQLAlchemy, SQLite |
| ML Engine | scikit-learn (Isolation Forest) |
| Auth | JWT, bcrypt, Google OAuth 2.0 |
| Frontend | Vanilla JS, Chart.js, CSS3 |
| Config | Pydantic Settings, dotenv |

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/FinGuard-Financial-Decision-Engine.git
cd FinGuard-Financial-Decision-Engine

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

Then open **http://localhost:5000** in your browser.

## 📁 Project Structure

```
├── app.py                  # Flask API server + routes
├── model.py                # Isolation Forest ML model
├── financial_analyzer.py   # 8 analytical modules
├── database.py             # SQLAlchemy models
├── config.py               # Environment-based settings
├── train_model.py          # Model training script
├── models/
│   ├── fraud_model.pkl     # Trained ML model
│   └── model_metadata.pkl  # Model metadata
├── static/
│   ├── css/style.css       # UI styling
│   └── js/app.js           # Frontend logic
├── templates/
│   └── index.html          # Main HTML template
├── requirements.txt
└── .env                    # Environment variables (not tracked)
```

## 🧠 ML Model Performance

| Metric | Score |
|--------|-------|
| Overall Accuracy | 100% |
| Anomaly Detection Rate | 100% |
| False Positive Rate | 0% |
| F1-Score | 1.00 |

## 📸 Demo

The landing page includes a live demo preview with sample data. Sign up or log in to access your personal financial dashboard.

**Demo credentials:** `demo@finguard.com` / `demo123`

## 📄 License

MIT License — feel free to use and modify.
