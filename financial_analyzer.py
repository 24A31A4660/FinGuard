"""
Financial Analyzer — AI Financial Behavior Analyzer
=====================================================
8 deterministic, rule-based modules for spending analysis.
Same input always produces the same output.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ─── MODULE 1: SPENDING ANALYSIS ─────────────────────────────────────────────────

def spending_analysis(df):
    """Calculate totals, percentages, and identify top categories."""
    total = float(df["amount"].sum())
    cat_totals = df.groupby("category")["amount"].sum().to_dict()
    cat_pct = {k: round(v / total * 100, 1) for k, v in cat_totals.items()} if total > 0 else {}

    sorted_cats = sorted(cat_totals.items(), key=lambda x: x[1], reverse=True)
    highest = sorted_cats[0][0] if sorted_cats else "N/A"
    top_2 = [c[0] for c in sorted_cats[:2]]

    return {
        "total_spending": round(total, 2),
        "category_totals": {k: round(v, 2) for k, v in cat_totals.items()},
        "category_percentages": cat_pct,
        "highest_spending_category": highest,
        "top_2_categories": top_2,
        "transaction_count": len(df),
        "avg_transaction": round(total / len(df), 2) if len(df) > 0 else 0,
    }


# ─── MODULE 2: TREND ANALYSIS ────────────────────────────────────────────────────

def trend_analysis(df):
    """Compare last 7 days vs previous 7 days to detect trends and spikes."""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    today = df["date"].max()

    last_7 = df[df["date"] > today - timedelta(days=7)]
    prev_7 = df[(df["date"] > today - timedelta(days=14)) & (df["date"] <= today - timedelta(days=7))]

    last_7_total = float(last_7["amount"].sum())
    prev_7_total = float(prev_7["amount"].sum())

    if prev_7_total == 0:
        trend = "stable"
        change_pct = 0.0
    else:
        change_pct = round((last_7_total - prev_7_total) / prev_7_total * 100, 1)
        if change_pct > 15:
            trend = "increasing"
        elif change_pct < -15:
            trend = "decreasing"
        else:
            trend = "stable"

    # Weekend spike detection
    df["day_of_week"] = df["date"].dt.dayofweek
    weekend = df[df["day_of_week"] >= 5]
    weekday = df[df["day_of_week"] < 5]
    avg_weekend = float(weekend["amount"].mean()) if len(weekend) > 0 else 0
    avg_weekday = float(weekday["amount"].mean()) if len(weekday) > 0 else 0
    weekend_spike = avg_weekend > avg_weekday * 1.3

    # Irregular spike detection (any day > 2x average)
    daily = df.groupby("date")["amount"].sum()
    avg_daily = float(daily.mean())
    spike_days = daily[daily > avg_daily * 2.0]
    irregular_spikes = [
        {"date": str(d.date()), "amount": round(float(v), 2)}
        for d, v in spike_days.items()
    ]

    return {
        "trend": trend,
        "change_percent": change_pct,
        "last_7_days_total": round(last_7_total, 2),
        "prev_7_days_total": round(prev_7_total, 2),
        "weekend_spending_spike": weekend_spike,
        "avg_weekend_spending": round(avg_weekend, 2),
        "avg_weekday_spending": round(avg_weekday, 2),
        "irregular_spikes": irregular_spikes,
    }


# ─── MODULE 3: FINANCIAL PERSONALITY ─────────────────────────────────────────────

def financial_personality(df, monthly_income=50000):
    """Classify user personality based on deterministic rules."""
    total = float(df["amount"].sum())
    days = max((pd.to_datetime(df["date"]).max() - pd.to_datetime(df["date"]).min()).days, 1)
    projected_monthly = total / days * 30

    savings_rate = max(0, (monthly_income - projected_monthly) / monthly_income * 100)

    cat_totals = df.groupby("category")["amount"].sum()
    shopping_ratio = float(cat_totals.get("Shopping", 0)) / total * 100 if total > 0 else 0

    daily_totals = df.groupby(pd.to_datetime(df["date"]).dt.date)["amount"].sum()
    spending_variance = float(daily_totals.std()) if len(daily_totals) > 1 else 0
    avg_daily = float(daily_totals.mean()) if len(daily_totals) > 0 else 1
    cv = spending_variance / avg_daily if avg_daily > 0 else 0  # coefficient of variation

    if savings_rate > 30:
        ptype = "Saver"
        reason = f"You save {savings_rate:.0f}% of your income — excellent financial discipline."
    elif shopping_ratio > 40:
        ptype = "Impulsive Spender"
        reason = f"Shopping accounts for {shopping_ratio:.0f}% of your spending — consider budgeting limits."
    elif cv > 1.2:
        ptype = "Risky Spender"
        reason = f"High spending variance (CV: {cv:.1f}) indicates unpredictable financial behavior."
    else:
        ptype = "Balanced"
        reason = "Your spending is well-distributed across categories with consistent daily patterns."

    return {
        "type": ptype,
        "reason": reason,
        "savings_rate": round(savings_rate, 1),
        "shopping_ratio": round(shopping_ratio, 1),
        "spending_variance": round(spending_variance, 2),
        "monthly_income": monthly_income,
        "projected_monthly_spending": round(projected_monthly, 2),
    }


# ─── MODULE 4: FUTURE SPENDING PREDICTION ────────────────────────────────────────

def spending_prediction(df):
    """Predict next 30-day spending using moving average."""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    daily = df.groupby("date")["amount"].sum().sort_index()

    if len(daily) < 3:
        return {
            "predicted_monthly_spending": 0,
            "overspending_risk": "LOW",
            "daily_average": 0,
            "confidence": "low",
        }

    # Use last 14 days if available, else all data
    window = min(14, len(daily))
    recent = daily.tail(window)
    daily_avg = float(recent.mean())
    predicted = daily_avg * 30

    # Risk classification
    if predicted > 45000:
        risk = "HIGH"
    elif predicted > 30000:
        risk = "MEDIUM"
    else:
        risk = "LOW"

    return {
        "predicted_monthly_spending": round(predicted, 2),
        "overspending_risk": risk,
        "daily_average": round(daily_avg, 2),
        "confidence": "high" if window >= 10 else "medium" if window >= 5 else "low",
        "window_days": window,
    }


# ─── MODULE 5: FINANCIAL HEALTH SCORE ────────────────────────────────────────────

def financial_health_score(df, monthly_income=50000):
    """Compute score (0-100) based on consistency, balance, and savings."""
    total = float(df["amount"].sum())
    days = max((pd.to_datetime(df["date"]).max() - pd.to_datetime(df["date"]).min()).days, 1)
    projected = total / days * 30

    # Savings penalty (0-40 points)
    savings_rate = max(0, (monthly_income - projected) / monthly_income)
    savings_penalty = max(0, (1 - savings_rate * 3.33)) * 40  # 30% savings → 0 penalty

    # Category imbalance penalty (0-30 points)
    cat_pct = df.groupby("category")["amount"].sum() / total * 100 if total > 0 else pd.Series()
    max_pct = float(cat_pct.max()) if len(cat_pct) > 0 else 0
    imbalance_penalty = max(0, (max_pct - 30) / 70 * 30)  # >30% single category penalized

    # Consistency penalty (0-30 points)
    daily = df.groupby(pd.to_datetime(df["date"]).dt.date)["amount"].sum()
    if len(daily) > 1:
        cv = float(daily.std() / daily.mean())
        consistency_penalty = min(30, cv * 20)
    else:
        consistency_penalty = 15

    score = max(0, min(100, 100 - savings_penalty - imbalance_penalty - consistency_penalty))

    if score >= 75:
        risk_level = "LOW"
    elif score >= 50:
        risk_level = "MEDIUM"
    else:
        risk_level = "HIGH"

    return {
        "score": round(score, 1),
        "risk_level": risk_level,
        "savings_penalty": round(savings_penalty, 1),
        "imbalance_penalty": round(imbalance_penalty, 1),
        "consistency_penalty": round(consistency_penalty, 1),
    }


# ─── MODULE 6: INSIGHT ENGINE ────────────────────────────────────────────────────

def insight_engine(df, monthly_income=50000):
    """Generate structured insights from spending data."""
    sa = spending_analysis(df)
    ta = trend_analysis(df)
    fp = financial_personality(df, monthly_income)

    key_issues = []
    behavior_patterns = []
    risk_factors = []

    # Key issues
    if sa["highest_spending_category"] == "Shopping" and sa["category_percentages"].get("Shopping", 0) > 30:
        key_issues.append(f"High spending in Shopping category ({sa['category_percentages']['Shopping']}% of total)")
    if sa["highest_spending_category"] == "Food" and sa["category_percentages"].get("Food", 0) > 35:
        key_issues.append(f"Food expenses are above recommended threshold ({sa['category_percentages']['Food']}%)")
    if fp["savings_rate"] < 20:
        key_issues.append(f"Savings rate is only {fp['savings_rate']}% — below the recommended 20% minimum")
    if ta["change_percent"] > 20:
        key_issues.append(f"Spending increased by {ta['change_percent']}% in the last 7 days")

    # Behavior patterns
    if ta["weekend_spending_spike"]:
        behavior_patterns.append("Weekend spending is significantly higher than weekday spending")
    if ta["trend"] == "increasing":
        behavior_patterns.append("Spending trend is upward — expenses are growing week-over-week")
    elif ta["trend"] == "decreasing":
        behavior_patterns.append("Spending trend is downward — good progress on cost reduction")
    behavior_patterns.append(f"Financial personality: {fp['type']} — {fp['reason']}")

    if len(ta["irregular_spikes"]) > 0:
        behavior_patterns.append(f"{len(ta['irregular_spikes'])} irregular spending spike(s) detected")

    # Risk factors
    if fp["projected_monthly_spending"] > monthly_income * 0.9:
        risk_factors.append("Projected monthly spending exceeds 90% of income — minimal savings buffer")
    if fp["shopping_ratio"] > 30:
        risk_factors.append(f"Shopping is {fp['shopping_ratio']}% of spending — discretionary risk")
    if len(ta["irregular_spikes"]) > 2:
        risk_factors.append("Multiple irregular spikes increase financial unpredictability")
    if ta["change_percent"] > 30:
        risk_factors.append(f"Rapid spending acceleration ({ta['change_percent']}%) may be unsustainable")

    if not key_issues:
        key_issues.append("No critical spending issues detected — finances are on track")
    if not risk_factors:
        risk_factors.append("No significant risk factors identified")

    return {
        "key_issues": key_issues,
        "behavior_patterns": behavior_patterns,
        "risk_factors": risk_factors,
    }


# ─── MODULE 7: RECOMMENDATION ENGINE ─────────────────────────────────────────────

def recommendation_engine(df, monthly_income=50000):
    """Generate rule-based, actionable recommendations."""
    sa = spending_analysis(df)
    fp = financial_personality(df, monthly_income)
    pred = spending_prediction(df)
    recs = []

    # Category-specific recommendations
    cat_pct = sa["category_percentages"]
    if cat_pct.get("Food", 0) > 35:
        target = round(sa["category_totals"]["Food"] * 0.85, 0)
        recs.append({
            "category": "Food",
            "action": f"Reduce food spending by 15% to ₹{target:,.0f}",
            "priority": "HIGH",
            "impact": "Can save ₹" + f"{sa['category_totals']['Food'] - target:,.0f}",
        })
    if cat_pct.get("Shopping", 0) > 25:
        weekly_limit = round(sa["category_totals"]["Shopping"] / 4 * 0.7, 0)
        recs.append({
            "category": "Shopping",
            "action": f"Limit shopping expenses to ₹{weekly_limit:,.0f} per week",
            "priority": "HIGH",
            "impact": "30% reduction in discretionary spending",
        })
    if cat_pct.get("Entertainment", 0) > 15:
        recs.append({
            "category": "Entertainment",
            "action": "Cap entertainment to 10% of monthly income (₹5,000)",
            "priority": "MEDIUM",
            "impact": "Better allocation toward savings",
        })

    # Savings recommendations
    if fp["savings_rate"] < 20:
        target_savings = round(monthly_income * 0.2)
        recs.append({
            "category": "Savings",
            "action": f"Increase savings to at least ₹{target_savings:,.0f}/month (20% of income)",
            "priority": "HIGH",
            "impact": f"Current savings rate is only {fp['savings_rate']}%",
        })
    elif fp["savings_rate"] < 30:
        recs.append({
            "category": "Savings",
            "action": "Consider increasing savings to 30% for long-term financial security",
            "priority": "MEDIUM",
            "impact": "Build an emergency fund within 6 months",
        })

    # Prediction-based recommendations
    if pred["overspending_risk"] == "HIGH":
        recs.append({
            "category": "Overall",
            "action": f"Projected spending is ₹{pred['predicted_monthly_spending']:,.0f} — reduce discretionary expenses immediately",
            "priority": "CRITICAL",
            "impact": "Prevent month-end deficit",
        })

    if not recs:
        recs.append({
            "category": "General",
            "action": "Maintain current spending patterns — financial health is good",
            "priority": "LOW",
            "impact": "Continue building savings and emergency fund",
        })

    return recs


# ─── MODULE 8: WHAT-IF SIMULATION ────────────────────────────────────────────────

def whatif_simulation(df, monthly_income=50000, adjust_category=None, adjust_percent=0):
    """Simulate the effect of adjusting spending in a category."""
    df_sim = df.copy()
    original_score = financial_health_score(df, monthly_income)
    original_pred = spending_prediction(df)

    if adjust_category and adjust_category in df_sim["category"].values:
        mask = df_sim["category"] == adjust_category
        factor = 1 + (adjust_percent / 100)
        df_sim.loc[mask, "amount"] = df_sim.loc[mask, "amount"] * factor

    new_score = financial_health_score(df_sim, monthly_income)
    new_pred = spending_prediction(df_sim)

    original_total = float(df["amount"].sum())
    new_total = float(df_sim["amount"].sum())

    return {
        "original_score": original_score["score"],
        "new_score": new_score["score"],
        "score_change": round(new_score["score"] - original_score["score"], 1),
        "original_monthly": original_pred["predicted_monthly_spending"],
        "new_monthly": new_pred["predicted_monthly_spending"],
        "spending_change": round(new_total - original_total, 2),
        "category_adjusted": adjust_category or "None",
        "adjustment_percent": adjust_percent,
    }


# ─── MASTER ANALYSIS FUNCTION ────────────────────────────────────────────────────

def analyze_financial_behavior(df, monthly_income=50000):
    """Run all 8 modules and return the complete analysis."""
    return {
        "spending_analysis": spending_analysis(df),
        "trend_analysis": trend_analysis(df),
        "financial_personality": financial_personality(df, monthly_income),
        "spending_prediction": spending_prediction(df),
        "financial_health_score": financial_health_score(df, monthly_income),
        "insights": insight_engine(df, monthly_income),
        "recommendations": recommendation_engine(df, monthly_income),
    }
