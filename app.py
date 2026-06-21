import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

# ==========================================
# 1. PAGE CONFIGURATION & THEME
# ==========================================
st.set_page_config(
    page_title="Personal Finance Dashboard & Analyzer",
    page_icon="💰",
    layout="wide"
)

DATA_DIR = "data"
DATA_PATH = os.path.join(DATA_DIR, "transactions.csv")

# ==========================================
# 2. BACKEND DATA ENGINE (PANDAS)
# ==========================================
def initialize_dummy_data():
    """Generates a starter dataset if no database exists yet."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        
    dummy_data = {
        "Date": ["2026-06-01", "2026-06-03", "2026-06-05", "2026-06-10", "2026-06-15", "2026-06-20"],
        "Category": ["Salary", "Groceries", "Rent", "Freelance", "Dining Out", "Streaming Services"],
        "Type": ["Income", "Expense", "Expense", "Income", "Expense", "Expense"],
        "Amount": [50000.0, 1500.50, 12000.0, 4500.0, 850.20, 150.99],
        "Description": ["Monthly Corporate Salary", "Weekly Supermarket Run", "Apartment Rent", "Web dev gig payment", "Dinner with friends", "Netflix subscription"]
    }
    df = pd.DataFrame(dummy_data)
    df.to_csv(DATA_PATH, index=False)

if not os.path.exists(DATA_PATH):
    initialize_dummy_data()

@st.cache_data
def load_data(file_path):
    """Loads CSV and ensures explicit data types."""
    df = pd.read_csv(file_path)
    df["Date"] = pd.to_datetime(df["Date"])
    df["Amount"] = pd.to_numeric(df["Amount"])
    return df

def save_data(df, file_path):
    """Saves DataFrame modifications back to persistent storage."""
    df.to_csv(file_path, index=False)

# Read current state of data
df = load_data(DATA_PATH)

# ==========================================
# 3. FRONTEND USER INTERFACE
# ==========================================
st.title("💸 Personal Finance Dashboard & Analyzer")
st.markdown("Track your cash flow, analyze spending allocations, and optimize your saving habits.")
st.write("---")

# SIDEBAR: Transaction Intake Form
st.sidebar.header("📥 Log New Transaction")
with st.sidebar.form("transaction_form", clear_on_submit=True):
    tx_date = st.date_input("Date", datetime.now())
    tx_type = st.selectbox("Type", ["Expense", "Income"])
    tx_category = st.selectbox("Category", [
        "Salary", "Freelance", "Investments", 
        "Groceries", "Rent", "Utilities", 
        "Dining Out", "Entertainment", "Misc"
    ])
    tx_amount = st.number_input("Amount", min_value=0.01, step=100.0)
    tx_desc = st.text_input("Description", placeholder="e.g., Grocery store run")
    
    submit_button = st.form_submit_button(label="Add Transaction")

# Form submission logic (With Smart Income Fallback)
if submit_button:
    # Rule 1: Expenses still strictly require a manual description
    if tx_type == "Expense" and tx_desc.strip() == "":
        st.sidebar.error("⚠️ Please type a description before adding an expense!")
    else:
        # Rule 2: Income bypasses the error. If left blank, it generates a clean label automatically.
        if tx_desc.strip() == "":
            final_desc = f"{tx_category} Credit"
        else:
            final_desc = tx_desc.strip()

        new_row = pd.DataFrame([{
            "Date": tx_date.strftime("%Y-%m-%d"),
            "Category": tx_category,
            "Type": tx_type,
            "Amount": tx_amount,
            "Description": final_desc
        }])
        
        # Reload from disk, append new entry, and save back
        current_df = pd.read_csv(DATA_PATH)
        updated_df = pd.concat([current_df, new_row], ignore_index=True)
        save_data(updated_df, DATA_PATH)
        
        st.sidebar.success("Transaction recorded successfully!")
        
        # Clear the cache so the app reads the newly saved data
        load_data.clear() 
        st.rerun()

# ==========================================
# 4. DATA ANALYSIS & KPI METRICS
# ==========================================
total_income = df[df["Type"] == "Income"]["Amount"].sum()
total_expense = df[df["Type"] == "Expense"]["Amount"].sum()
net_savings = total_income - total_expense
savings_rate = (net_savings / total_income * 100) if total_income > 0 else 0

# Display High-Level Cards (Formatted with ₹)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Income", f"₹{total_income:,.2f}")
col2.metric("Total Expenses", f"₹{total_expense:,.2f}")
col3.metric("Net Savings", f"₹{net_savings:,.2f}")
col4.metric("Savings Rate", f"{savings_rate:.1f}%")

st.write("---")

# ==========================================
# 5. DATA VISUALIZATION LAYER
# ==========================================
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("📊 Expense Allocation by Category")
    expense_df = df[df["Type"] == "Expense"]
    if not expense_df.empty:
        category_pie = px.pie(
            expense_df, 
            values="Amount", 
            names="Category", 
            hole=0.4,
            color_discrete_sequence=px.colors.sequential.RdBu
        )
        st.plotly_chart(category_pie, use_container_width=True)
    else:
        st.info("No expense data found. Log your expenses to view distribution.")

with chart_col2:
    st.subheader("📈 Cash Flow Timeline")
    if not df.empty:
        time_df = df.copy()
        time_df["Month-Year"] = time_df["Date"].dt.to_period("M").astype(str)
        cash_flow = time_df.groupby(["Month-Year", "Type"])["Amount"].sum().reset_index()
        
        cash_bar = px.bar(
            cash_flow, 
            x="Month-Year", 
            y="Amount", 
            color="Type", 
            barmode="group",
            color_discrete_map={"Income": "#2ecc71", "Expense": "#e74c3c"}
        )
        st.plotly_chart(cash_bar, use_container_width=True)
    else:
        st.info("Insufficient timeline historical records available.")

st.write("---")

# ==========================================
# 6. RAW DATA LEDGER
# ==========================================
st.subheader("📋 Historical Transaction Ledger")
if not df.empty:
    # Render table with newest items first (Formatted with ₹)
    display_df = df.sort_values(by="Date", ascending=False)
    st.dataframe(display_df.style.format({"Amount": "₹{:,.2f}"}), use_container_width=True)
    
    # Reset Database Feature
    st.write("")
    if st.button("Reset Database to Default"):
        initialize_dummy_data()
        load_data.clear() 
        st.rerun()
else:
    st.warning("The transaction log ledger is empty.")