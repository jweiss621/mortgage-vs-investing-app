import streamlit as st
import pandas as pd

def after_tax_return(pre_tax_return, asset_mix, tax_rates):
    equity_return = pre_tax_return * asset_mix
    fixed_income_return = pre_tax_return * (1 - asset_mix)
    equity_after_tax = equity_return * (1 - tax_rates['capital_gains'])
    fixed_income_after_tax = fixed_income_return * (1 - tax_rates['interest'])
    return equity_after_tax + fixed_income_after_tax

def amortization_schedule(balance, rate, years):
    schedule = []
    monthly_rate = rate / 12
    months = years * 12
    monthly_payment = balance * (monthly_rate * (1 + monthly_rate) ** months) / ((1 + monthly_rate) ** months - 1)

    for year in range(1, years + 1):
        interest_paid = 0
        principal_paid = 0
        for _ in range(12):
            interest = balance * monthly_rate
            principal = monthly_payment - interest
            balance -= principal
            interest_paid += interest
            principal_paid += principal
        schedule.append({
            'Year': year,
            'Remaining Mortgage': balance,
            'Principal Paid': principal_paid,
            'Interest Paid': interest_paid,
            'Annual Payment': monthly_payment * 12
        })
    return pd.DataFrame(schedule)

def investment_growth(initial_amount, annual_return, years, annual_contribution=0):
    values = []
    value = initial_amount
    for year in range(1, years + 1):
        value *= (1 + annual_return)
        value += annual_contribution
        values.append({'Year': year, 'Investment Value': value})
    return pd.DataFrame(values)

# Streamlit App UI
st.title("🏠 Invest vs. Mortgage Paydown Simulator")

st.sidebar.header("Input Parameters")

investable_assets = st.sidebar.number_input("💼 Investable Assets ($)", value=100000, step=1000)
mortgage_balance = st.sidebar.number_input("🏦 Mortgage Balance Remaining ($)", value=400000, step=1000)
mortgage_rate = st.sidebar.number_input("💸 Mortgage Interest Rate (%)", value=5.0, step=0.1) / 100
amortization_years = st.sidebar.slider("⏳ Remaining Amortization Period (Years)", 5, 30, 20)
pre_tax_return = st.sidebar.number_input("📈 Expected Pre-Tax Return on Investment (%)", value=6.0, step=0.1) / 100
asset_mix = st.sidebar.slider("📊 Equity Allocation (%)", 0, 100, 70) / 100
home_value = st.sidebar.number_input("🏡 Home Value ($)", value=800000, step=10000)
paydown_amount = st.sidebar.number_input("💰 Amount Used to Pay Down Mortgage ($)", value=50000, min_value=0, max_value=int(investable_assets), step=1000)
tax_rate_interest = st.sidebar.number_input("🧾 Tax Rate on Interest Income (%)", value=53.0, step=0.5) / 100
tax_rate_cap_gains = st.sidebar.number_input("💹 Tax Rate on Capital Gains (%)", value=26.5, step=0.5) / 100

tax_rates = {'interest': tax_rate_interest, 'capital_gains': tax_rate_cap_gains}
after_tax_return_rate = after_tax_return(pre_tax_return, asset_mix, tax_rates)

st.markdown(f"### 📊 After-Tax Rate of Return: **{after_tax_return_rate * 100:.2f}%**")

# Scenario 1: Invest All
schedule_invest = amortization_schedule(mortgage_balance, mortgage_rate, amortization_years)
investment_invest = investment_growth(investable_assets, after_tax_return_rate, amortization_years)
schedule_invest['Investment Value'] = investment_invest['Investment Value']
schedule_invest['Net Worth (Invest)'] = schedule_invest['Investment Value'] + home_value - schedule_invest['Remaining Mortgage']

# Scenario 2: Paydown Mortgage + Invest Remaining + Reinvest Mortgage Savings
remaining_assets_paydown = investable_assets - paydown_amount
reduced_mortgage = mortgage_balance - paydown_amount
schedule_paydown = amortization_schedule(reduced_mortgage, mortgage_rate, amortization_years)
baseline_payment = schedule_invest.loc[0, 'Annual Payment']
reduced_payment = schedule_paydown.loc[0, 'Annual Payment']
annual_savings = baseline_payment - reduced_payment

investment_paydown = investment_growth(remaining_assets_paydown, after_tax_return_rate, amortization_years, annual_contribution=annual_savings)
schedule_paydown['Investment Value'] = investment_paydown['Investment Value']
schedule_paydown['Net Worth (Paydown)'] = schedule_paydown['Investment Value'] + home_value - schedule_paydown['Remaining Mortgage']

# Combined Results
comparison = pd.DataFrame({
    'Year': schedule_invest['Year'],
    'Net Worth (Invest)': schedule_invest['Net Worth (Invest)'],
    'Net Worth (Paydown)': schedule_paydown['Net Worth (Paydown)'],
})

st.line_chart(comparison.set_index('Year'))
st.dataframe(comparison)
