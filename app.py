import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Gold Price & LTV Risk Dashboard",
                   layout="wide",
                   page_icon="💰")

# -----------------------------
# Load Data
# -----------------------------
@st.cache_data
def load_data():
    ts = pd.read_csv("gold_price_ts_daily.csv", parse_dates=["Date"])
    forecast = pd.read_csv("gold_price_forecast_90d.csv", parse_dates=["Date"])
    combined = pd.read_csv("gold_price_history_and_forecast.csv", parse_dates=["Date"])
    loan_df = pd.read_csv("Dataset/simulated_loan_portfolio.csv", parse_dates=["disbursal_date"])
    return ts, forecast, combined, loan_df

ts, forecast, combined, loan_df = load_data()

# -----------------------------
# Sidebar Filters
# -----------------------------
st.sidebar.header("Filters")

loan_amount_min = st.sidebar.number_input("Min Loan Amount", value=0, step=1000)
loan_amount_max = st.sidebar.number_input("Max Loan Amount", value=300000, step=1000)

filtered_loans = loan_df[
    (loan_df["loan_amount"] >= loan_amount_min) &
    (loan_df["loan_amount"] <= loan_amount_max)
]

st.sidebar.markdown("---")
scenario = st.sidebar.selectbox("Stress Test Scenario",
                                ["None", "-5%", "-10%", "-20%"])

stress_factor = {
    "None": 1.0,
    "-5%": 0.95,
    "-10%": 0.90,
    "-20%": 0.80
}[scenario]

# -----------------------------
# Page Title
# -----------------------------
st.title("💰 Gold Price Impact & LTV Risk Dashboard")

# =============================
# SECTION 1 — GOLD PRICE TREND
# =============================
st.header("📈 Gold Price — Historical + Forecast")

fig1 = px.line(combined, x="Date", y=["Historical", "Forecast"],
               labels={"value": "Price (INR/10g)", "Date": "Date"},
               title="Gold Price Trend & 90-Day Forecast")

st.plotly_chart(fig1, use_container_width=True)

# =============================
# SECTION 2 — PORTFOLIO OVERVIEW
# =============================
st.header("🏦 Loan Portfolio Overview")

col1, col2, col3 = st.columns(3)
col1.metric("Total Loans", len(filtered_loans))
col2.metric("Avg Loan Amount", f"{filtered_loans['loan_amount'].mean():,.0f} INR")
col3.metric("Avg LTV (Now)", f"{filtered_loans['LTV_now'].mean():.1f}%")

# =============================
# SECTION 3 — LTV DISTRIBUTION
# =============================
st.header("📊 LTV Distribution")

fig2 = px.histogram(filtered_loans, x="LTV_now", nbins=40,
                    title="Current LTV Distribution",
                    labels={"LTV_now": "LTV (%)"})

fig2.add_vline(x=75, line_dash="dash", line_color="red",
               annotation_text="RBI 75% Limit")

st.plotly_chart(fig2, use_container_width=True)

# =============================
# SECTION 4 — STRESS TEST
# =============================
st.header("⚠️ Stress Test (LTV Under Price Shocks)")

current_price_g = ts["Gold_Price"].iloc[-1] / 10
shock_price_g = current_price_g * stress_factor

filtered_loans["gold_value_shock"] = (
    filtered_loans["gold_weight_g"] *
    filtered_loans["purity_factor"] *
    shock_price_g
)

filtered_loans["LTV_shock"] = (
    filtered_loans["loan_amount"] /
    filtered_loans["gold_value_shock"]
) * 100

st.subheader(f"Scenario Selected: {scenario}")
st.metric("Loans Breaching 75% LTV", (filtered_loans["LTV_shock"] > 75).sum())

fig3 = px.histogram(filtered_loans, x="LTV_shock", nbins=40,
                    title=f"LTV Distribution Under {scenario} Shock")

fig3.add_vline(x=75, line_dash="dash", line_color="red")

st.plotly_chart(fig3, use_container_width=True)

# =============================
# SECTION 5 — RISKIEST LOANS TABLE
# =============================
st.header("🔥 Top 20 Riskiest Loans")

top20 = filtered_loans.sort_values("LTV_shock", ascending=False).head(20)
st.dataframe(top20)
