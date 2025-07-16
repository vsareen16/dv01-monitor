import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(page_title="DV01 & Risk Dashboard", layout="wide")
st.title("📊 Firm-Level DV01 & Interest Rate Risk Dashboard")

uploaded_file = st.file_uploader("Upload Excel Position File", type=["xlsx"])

if uploaded_file:
    xls = pd.ExcelFile(uploaded_file)
    sheet_names = xls.sheet_names

    # Load firm-level margin and capital from "FirmSummary" sheet
    margin_used = None
    capital = None
    if "FirmSummary" in sheet_names:
        firm_df = pd.read_excel(xls, sheet_name="FirmSummary", index_col=0)
        margin_used = firm_df.loc["Margin Used", "Value"]
        capital = firm_df.loc["Capital", "Value"]
        st.success(f"📦 Firm Margin: AUD {margin_used:,.0f} | 💰 Capital: AUD {capital:,.0f}")

    # Scenario stress table input (Tenor → Shift in bps)
    st.subheader("🔁 Curve Shift Scenario Input")
    scenario_shifts = {}
    all_tenors = set()
    for sheet in [s for s in sheet_names if s != "FirmSummary"]:
        df = pd.read_excel(xls, sheet_name=sheet)
        all_tenors.update(df["Tenor"].unique())
    all_tenors = sorted(list(all_tenors))
    shift_input = {tenor: st.number_input(f"Shift (bp) for {tenor}", value=0, step=1) for tenor in all_tenors}

    # Prepare combined stats
    combined_data = []

    for sheet in [s for s in sheet_names if s != "FirmSummary"]:
        st.subheader(f"📁 Trader: {sheet}")
        df = pd.read_excel(xls, sheet_name=sheet)
        df["Trader"] = sheet

        TICK_VALUE = 25
        DV01_LIMIT_PCT = 30

        df["DV01 (AUD/bp)"] = df["Contracts"] * TICK_VALUE
        df["Abs DV01"] = df["DV01 (AUD/bp)"].abs()
        df["% of Total DV01"] = df["Abs DV01"] / df["Abs DV01"].sum() * 100
        df["Limit Breach (>30%)"] = df["% of Total DV01"] > DV01_LIMIT_PCT
        df["Timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M")

        st.dataframe(df[["Tenor", "Contracts", "DV01 (AUD/bp)", "% of Total DV01", "Limit Breach (>30%)"]])

        fig, ax = plt.subplots()
        ax.bar(df["Tenor"], df["% of Total DV01"], color=df["Limit Breach (>30%)"].map({True: 'red', False: 'skyblue'}))
        ax.axhline(DV01_LIMIT_PCT, color='gray', linestyle='--')
        ax.set_title(f"DV01 Exposure % – {sheet}")
        ax.set_ylabel("% of Total DV01")
        ax.set_xticklabels(df["Tenor"], rotation=45)
        st.pyplot(fig)

        total_dv01 = df["DV01 (AUD/bp)"].sum()
        pnl_5bp = total_dv01 * 5
        pnl_10bp = total_dv01 * 10

        # Scenario stress calc
        df["Shift_bps"] = df["Tenor"].map(shift_input)
        df["Stress_PnL"] = df["DV01 (AUD/bp)"] * df["Shift_bps"]
        stress_pnl = df["Stress_PnL"].sum()

        # Directional messaging
        if pnl_5bp > 0:
            st.markdown(f"💰 **Total 5bp P&L (yields ↑)**: AUD {pnl_5bp:,.0f} 🔻 **Loss**")
        else:
            st.markdown(f"💰 **Total 5bp P&L (yields ↑)**: AUD {pnl_5bp:,.0f} 🟢 **Gain**")

        if pnl_10bp > 0:
            st.markdown(f"💰 **Total 10bp P&L (yields ↑)**: AUD {pnl_10bp:,.0f} 🔻 **Loss**")
        else:
            st.markdown(f"💰 **Total 10bp P&L (yields ↑)**: AUD {pnl_10bp:,.0f} 🟢 **Gain**")

        if stress_pnl > 0:
            st.markdown(f"🚨 **Scenario Stress P&L**: AUD {stress_pnl:,.0f} 🔻 **Loss**")
        else:
            st.markdown(f"🚨 **Scenario Stress P&L**: AUD {stress_pnl:,.0f} 🟢 **Gain**")

        if margin_used:
            st.markdown(f"📊 5bp P&L as % of Margin: {pnl_5bp / margin_used:.2%}")
            st.markdown(f"📊 10bp P&L as % of Margin: {pnl_10bp / margin_used:.2%}")
            st.markdown(f"📊 Stress P&L as % of Margin: {stress_pnl / margin_used:.2%}")
        if capital:
            st.markdown(f"📈 5bp P&L as % of Capital: {pnl_5bp / capital:.2%}")
            st.markdown(f"📈 10bp P&L as % of Capital: {pnl_10bp / capital:.2%}")
            st.markdown(f"📈 Stress P&L as % of Capital: {stress_pnl / capital:.2%}")

        combined_data.append({
            "Trader": sheet,
            "DV01": total_dv01,
            "PnL_5bp": pnl_5bp,
            "PnL_10bp": pnl_10bp,
            "Stress_PnL": stress_pnl
        })

    # Group Summary
    if combined_data:
        st.subheader("📊 Group-Level Summary")
        group_df = pd.DataFrame(combined_data)
        st.dataframe(group_df)

        total_firm_dv01 = group_df["DV01"].sum()
        firm_pnl_5bp = group_df["PnL_5bp"].sum()
        firm_pnl_10bp = group_df["PnL_10bp"].sum()
        firm_stress_pnl = group_df["Stress_PnL"].sum()

        if firm_pnl_5bp > 0:
            st.markdown(f"🧮 **Firm-wide 5bp P&L (yields ↑)**: AUD {firm_pnl_5bp:,.0f} 🔻 **Loss**")
        else:
            st.markdown(f"🧮 **Firm-wide 5bp P&L (yields ↑)**: AUD {firm_pnl_5bp:,.0f} 🟢 **Gain**")

        if firm_pnl_10bp > 0:
            st.markdown(f"🧮 **Firm-wide 10bp P&L (yields ↑)**: AUD {firm_pnl_10bp:,.0f} 🔻 **Loss**")
        else:
            st.markdown(f"🧮 **Firm-wide 10bp P&L (yields ↑)**: AUD {firm_pnl_10bp:,.0f} 🟢 **Gain**")

        if firm_stress_pnl > 0:
            st.markdown(f"⚠️ **Firm-wide Scenario Stress P&L**: AUD {firm_stress_pnl:,.0f} 🔻 **Loss**")
        else:
            st.markdown(f"⚠️ **Firm-wide Scenario Stress P&L**: AUD {firm_stress_pnl:,.0f} 🟢 **Gain**")

        if margin_used:
            st.markdown(f"📊 **Stress P&L as % Margin**: {firm_stress_pnl / margin_used:.2%}")
        if capital:
            st.markdown(f"📈 **Stress P&L as % Capital**: {firm_stress_pnl / capital:.2%}")
