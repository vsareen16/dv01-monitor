
import streamlit as st
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt

st.set_page_config(page_title="DV01 Risk Monitor", layout="wide")
st.title("📊 DV01 Risk Monitoring Dashboard")

uploaded_file = st.file_uploader("Upload Excel Position File", type=["xlsx"])

if uploaded_file:
    xls = pd.ExcelFile(uploaded_file)
    sheet_names = xls.sheet_names

    for sheet in sheet_names:
        st.subheader(f"📁 Trader Sheet: {sheet}")
        df = pd.read_excel(xls, sheet_name=sheet)
        
        TICK_VALUE = 25
        DV01_LIMIT_PCT = 30
        
        df["DV01 (AUD/bp)"] = df["Contracts"] * TICK_VALUE
        df["Abs DV01"] = df["DV01 (AUD/bp)"].abs()
        total_dv01 = df["Abs DV01"].sum()
        df["% of Total DV01"] = (df["Abs DV01"] / total_dv01) * 100
        df["Limit Breach (>30%)"] = df["% of Total DV01"] > DV01_LIMIT_PCT
        df["Timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M")

        st.dataframe(df)

        breaches = df[df["Limit Breach (>30%)"]]
        if not breaches.empty:
            st.warning("🚨 Limit breach detected:")
            st.dataframe(breaches)

        fig, ax = plt.subplots()
        bars = ax.bar(df["Tenor"], df["% of Total DV01"], color=df["Limit Breach (>30%)"].map({True: 'red', False: 'skyblue'}))
        ax.axhline(DV01_LIMIT_PCT, color='gray', linestyle='--')
        ax.set_title(f"DV01 % by Tenor — {sheet}")
        ax.set_ylabel("% of Total DV01")
        ax.set_xticklabels(df["Tenor"], rotation=45)
        st.pyplot(fig)

# --- Pull margin and capital from first row where it's not null
margin_used = df["Margin Used (AUD)"].dropna().iloc[0] if df["Margin Used (AUD)"].notna().any() else None
capital = df["Capital (AUD)"].dropna().iloc[0] if df["Capital (AUD)"].notna().any() else None

# --- P&L Impact Calculations
df["PnL_5bp (AUD)"] = df["DV01 (AUD/bp)"] * 5
df["PnL_10bp (AUD)"] = df["DV01 (AUD/bp)"] * 10

total_pnl_5bp = df["PnL_5bp (AUD)"].sum()
total_pnl_10bp = df["PnL_10bp (AUD)"].sum()

st.markdown(f"💰 **Total P&L Impact (5bp Move)**: AUD {total_pnl_5bp:,.0f}")
st.markdown(f"💰 **Total P&L Impact (10bp Move)**: AUD {total_pnl_10bp:,.0f}")

if margin_used:
    st.markdown(f"📊 **5bp P&L as % of Margin**: {total_pnl_5bp / margin_used:.2%}")
    st.markdown(f"📊 **10bp P&L as % of Margin**: {total_pnl_10bp / margin_used:.2%}")

if capital:
    st.markdown(f"📈 **5bp P&L as % of Capital**: {total_pnl_5bp / capital:.2%}")
    st.markdown(f"📈 **10bp P&L as % of Capital**: {total_pnl_10bp / capital:.2%}")
