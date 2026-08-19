import streamlit as st
import pandas as pd

st.set_page_config(page_title="Egyptian Real Estate Intelligence", layout="wide")
st.title("🏘️ Egyptian Real Estate Intelligence")
st.caption("Market overview based on self-collected data from Aqarmap — Greater Cairo")

df = pd.read_csv("dashboard_data/sale_gold.csv")
df = df[df["area"] != "unknown"]

min_listings = st.slider("Minimum listings per area", min_value=1, max_value=50, value=5)
filtered = df[df["listing_count"] >= min_listings].copy()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Listings", f"{filtered['listing_count'].sum():,}")
col2.metric("Areas Shown", len(filtered))
col3.metric("Avg Price", f"{filtered['avg_price'].mean():,.0f} EGP")
top_area = filtered.sort_values("avg_price_per_m2", ascending=False).iloc[0]
col4.metric("Priciest Area (per m²)", top_area["area"], f"{top_area['avg_price_per_m2']:,.0f} EGP/m²")

st.divider()

st.subheader("Market Data by Area")
display_df = filtered[["area", "listing_count", "avg_price", "avg_price_per_m2"]].copy()
display_df.columns = ["Area", "Listings", "Avg Price (EGP)", "Avg Price/m² (EGP)"]
display_df["Avg Price (EGP)"] = display_df["Avg Price (EGP)"].round(0).astype(int)
display_df["Avg Price/m² (EGP)"] = display_df["Avg Price/m² (EGP)"].round(0).astype(int)
st.dataframe(display_df.sort_values("Listings", ascending=False), use_container_width=True, hide_index=True)

st.divider()


st.subheader("Top 15 Areas by Price per m²")
chart_data = filtered.sort_values("avg_price_per_m2", ascending=False).head(15).set_index("area")["avg_price_per_m2"]
st.bar_chart(chart_data)