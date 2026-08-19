import streamlit as st
import pandas as pd

st.set_page_config(page_title="Deal Finder", layout="wide")
st.title("💰 Deal Finder")
st.caption("Listings priced below what the ML model predicts based on their specs")

df = pd.read_csv("dashboard_data/fair_value.csv")
df = df[df["area"] != "unknown"]

max_score = st.slider(
    "Show listings priced at least this much below predicted value (%)",
    min_value=5, max_value=90, value=20
)

deals = df[df["fair_value_score"] <= -max_score].copy()
deals = deals.sort_values("fair_value_score")

col1, col2 = st.columns(2)
col1.metric("Deals Found", len(deals))
col2.metric("Best Deal", f"{deals['fair_value_score'].min():.1f}%" if len(deals) > 0 else "N/A")

st.divider()

display_df = deals[["area", "price", "prediction", "fair_value_score", "url"]].copy()
display_df.columns = ["Area", "Actual Price (EGP)", "Predicted Price (EGP)", "Diff (%)", "Link"]
display_df["Actual Price (EGP)"] = display_df["Actual Price (EGP)"].round(0).astype(int)
display_df["Predicted Price (EGP)"] = display_df["Predicted Price (EGP)"].round(0).astype(int)

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
    column_config={"Link": st.column_config.LinkColumn("Listing")}
)