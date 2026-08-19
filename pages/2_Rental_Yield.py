import streamlit as st
import pandas as pd

st.set_page_config(page_title="Rental Yield", layout="wide")
st.title("📈 Rental Yield by Area")
st.caption("Estimated annual return if you buy and rent out an apartment, by area")

df = pd.read_csv("dashboard_data/rental_yield.csv")
df = df[df["area"] != "unknown"]

min_listings = st.slider("Minimum sale listings per area", min_value=1, max_value=50, value=5)
filtered = df[df["listing_count"] >= min_listings].copy()
filtered = filtered.sort_values("rental_yield_percent", ascending=False)

col1, col2, col3 = st.columns(3)
col1.metric("Areas Shown", len(filtered))
col2.metric("Best Yield", f"{filtered['rental_yield_percent'].max():.2f}%")
col3.metric("Avg Yield", f"{filtered['rental_yield_percent'].mean():.2f}%")

st.divider()

st.subheader("Top 15 Areas by Rental Yield")
chart_data = filtered.head(15).set_index("area")["rental_yield_percent"]
st.bar_chart(chart_data)

st.divider()

st.subheader("Full Data")
display_df = filtered[["area", "listing_count", "avg_price", "avg_monthly_rent", "rental_yield_percent"]].copy()
display_df.columns = ["Area", "Listings", "Avg Sale Price (EGP)", "Avg Monthly Rent (EGP)", "Annual Yield (%)"]
display_df["Avg Sale Price (EGP)"] = display_df["Avg Sale Price (EGP)"].round(0).astype(int)
display_df["Avg Monthly Rent (EGP)"] = display_df["Avg Monthly Rent (EGP)"].round(0).astype(int)
display_df["Annual Yield (%)"] = display_df["Annual Yield (%)"].round(2)

st.dataframe(display_df, use_container_width=True, hide_index=True)