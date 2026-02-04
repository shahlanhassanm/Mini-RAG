import streamlit as st
import pandas as pd
import requests
from sqlalchemy import create_engine
import sys
import os

# Add parent dir to path to import backend modules if needed, 
# but we will access DB directly or via API.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Database Connection
# We want to connect to crm.db in the parent directory (assn/crm.db)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "crm.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"
engine = create_engine(DATABASE_URL)

st.set_page_config(page_title="Payment Reminder Dashboard", layout="wide")

st.title("Admin Dashboard - Payment Reminders")

# Metrics
try:
    with engine.connect() as conn:
        invoices_df = pd.read_sql("SELECT * FROM invoices", conn)
        customers_df = pd.read_sql("SELECT * FROM customers", conn)
        logs_df = pd.read_sql("SELECT * FROM communication_logs", conn)
        orders_df = pd.read_sql("SELECT * FROM orders", conn)
        alerts_df = pd.read_sql("SELECT * FROM alerts", conn)

    col1, col2, col3 = st.columns(3)
    
    total_overdue = invoices_df[invoices_df['status'] == 'Overdue']['amount'].sum()
    overdue_count = len(invoices_df[invoices_df['status'] == 'Overdue'])
    messages_sent = len(logs_df)
    active_alerts = len(alerts_df[alerts_df['is_resolved'] == 0]) if not alerts_df.empty else 0

    col1.metric("Total Overdue Amount", f"${total_overdue:,.2f}")
    col2.metric("Overdue Invoices", overdue_count)
    col3.metric("Active Team Alerts", active_alerts)

    st.divider()

    # Manual Trigger
    st.subheader("Actions")
    if st.button("Run Manual Payment Check & Reminders"):
        try:
            # Assuming backend is running on 8000
            response = requests.post("http://localhost:8000/trigger-reminders")
            if response.status_code == 200:
                st.success(f"Triggered! {response.json()['count']} messages processed.")
                st.rerun() # Refresh data
            else:
                st.error(f"Failed: {response.text}")
        except Exception as e:
            st.error(f"Connection Error: {e}. Is the backend running?")

    col_inv, col_logs = st.columns(2)

    with col_inv:
        st.subheader("Overdue Invoices")
        overdue_df = invoices_df[invoices_df['status'] == 'Overdue']
        st.dataframe(overdue_df)

    # Internal Alerts Section
    st.divider()
    st.subheader("🚨 Internal Team Alerts (Finance/Sales)")
    if not alerts_df.empty and active_alerts > 0:
        active_alerts_df = alerts_df[alerts_df['is_resolved'] == 0]
        for index, row in active_alerts_df.iterrows():
            st.error(f"**{row['type']}**: {row['message']} (Date: {row['timestamp']})")
    else:
        st.success("No active alerts. Good job!")

    # Orders Section
    st.divider()
    st.subheader("📦 Order Delivery Status")
    st.dataframe(orders_df)

    with col_logs:
        st.subheader("Communication Logs")
        if not logs_df.empty:
            st.dataframe(logs_df.sort_values(by="timestamp", ascending=False))
        else:
            st.info("No communications yet.")
            
except Exception as e:
    st.error(f"Could not connect to database or read data. Make sure the backend has started at least once to create the DB. {e}")

