
import streamlit as st
import pandas as pd
import numpy as np
import numpy_financial as npf

# --- Page Setup ---
st.set_page_config(page_title="Mortgage vs. Investing Tool", layout="wide")
st.title("🏡 Mortgage vs. Investing Comparison Tool")

# --- Sidebar Inputs ---
st.sidebar.header("Assumptions")
purchase_price = st.sidebar.number_input("Home Purchase Price", value=1_300_000)
available_assets = st.sidebar.number_input("Available Assets", value=1_000_000)
down_payment_a = st.sidebar.number_input("Down Payment (Scenario A)", value=450_000)
down_payment_b = st.sidebar.number_input("Down Payment (Scenario B)", value=700_000)
mortgage_rate = st.sidebar.number_input("Mortgage Rate (%)", value=5.0) / 100
before_tax_return = st.sidebar.number_input("Before-Tax Investment Return (%)", value=7.0) / 100
amort_years = st.sidebar.slider("Amortization Period (Years)", 5, 30, 25)

# --- Asset Mix Inputs ---
st.sidebar.subheader("Asset Mix (Must Add to 100%)")
equity_pct = st.sidebar.slider("Equity %", 0, 100, 60)
fixed_income_pct = 100 - equity_pct
st.sidebar.write(f"Fixed Income %: {fixed_income_pct}")

# --- After-Tax Rate Logic ---
# Approximate tax rates (Ontario top bracket): 50% on interest, 25% on capital gains, 39% on eligible dividends
# Assume equity return: 50% capital gains, 50% dividends
equity_after_tax = before_tax_return * (0.5 * (1 - 0.25) + 0.5 * (1 - 0.39))
fixed_income_after_tax = before_tax_return * (1 - 0.50)
after_tax_return = (equity_pct / 100) * equity_after_tax + (fixed_income_pct / 100) * fixed_income_after_tax

# --- Calculations ---
months = amort_years * 12
r_monthly = mortgage_rate / 12
inv_monthly = (1 + after_tax_return) ** (1/12) - 1

def amortization_schedule(principal, rate, n_periods):
    payment = npf.pmt(rate, n_periods, -principal)
    schedule = []
    balance = principal
    for month in range(1, n_periods + 1):
        interest = balance * rate
        principal_paid = payment - interest
        balance -= principal_paid
        schedule.append((month, payment, principal_paid, interest, max(balance, 0)))
    return pd.DataFrame(schedule, columns=["Month", "Payment", "Principal", "Interest", "Balance"])

mortgage_a = purchase_price - down_payment_a
mortgage_b = purchase_price - down_payment_b
invested_a = available_assets - down_payment_a
invested_b = available_assets - down_payment_b

df_a = amortization_schedule(mortgage_a, r_monthly, months)
df_b = amortization_schedule(mortgage_b, r_monthly, months)

# Reinvest mortgage savings in Scenario B
pmt_diff = df_a["Payment"].iloc[0] - df_b["Payment"].iloc[0]
investment_a = []
investment_b = []
inv_a = invested_a
inv_b = invested_b

for m in range(months):
    inv_a *= (1 + inv_monthly)
    inv_b = inv_b * (1 + inv_monthly) + pmt_diff
    investment_a.append(inv_a)
    investment_b.append(inv_b)

df_a["Investment"] = investment_a
df_b["Investment"] = investment_b

df_a["Home Equity"] = purchase_price - df_a["Balance"]
df_b["Home Equity"] = purchase_price - df_b["Balance"]
df_a["Net Worth"] = df_a["Home Equity"] + df_a["Investment"]
df_b["Net Worth"] = df_b["Home Equity"] + df_b["Investment"]

# --- Output ---
st.subheader("📈 Net Worth Over Time")
net_worth_df = pd.DataFrame({
    "Month": df_a["Month"],
    "Scenario A (Lower Down, More Invested)": df_a["Net Worth"],
    "Scenario B (Higher Down)": df_b["Net Worth"]
})
st.line_chart(net_worth_df.set_index("Month"))

# Optional data view
with st.expander("📊 Show Full Data"):
    st.write(net_worth_df)

# Show calculated after-tax return
st.sidebar.markdown("---")
st.sidebar.metric("After-Tax Investment Return", f"{after_tax_return * 100:.2f}%")
