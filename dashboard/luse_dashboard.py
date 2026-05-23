import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="LuSE Market Analytics",
    layout="wide"
)

st.title("LuSE Market Analytics Dashboard")

df = pd.read_csv("data/processed/luse_historical_prices_clean.csv")

df["date"] = pd.to_datetime(df["date"])
df["price"] = pd.to_numeric(df["price"], errors="coerce")
df["volume"] = pd.to_numeric(df["volume"], errors="coerce")

ticker = st.selectbox(
    "Select a company",
    sorted(df["ticker"].unique())
)

company_df = df[df["ticker"] == ticker]

st.subheader(f"{ticker} Historical Share Price")

fig = px.line(
    company_df,
    x="date",
    y="price",
    title=f"{ticker} Historical Share Price"
)

st.plotly_chart(fig, use_container_width=True)

st.subheader("Key Metrics")

latest_price = company_df.sort_values("date")["price"].iloc[-1]
first_price = company_df.sort_values("date")["price"].iloc[0]
total_return = ((latest_price - first_price) / first_price) * 100
total_volume = company_df["volume"].sum()
volatility = company_df["daily_return"].std() * 100

col1, col2, col3, col4 = st.columns(4)

col1.metric("Latest Price", f"{latest_price:,.2f}")
col2.metric("Total Return", f"{total_return:,.2f}%")
col3.metric("Total Volume", f"{total_volume:,.0f}")
col4.metric("Volatility", f"{volatility:,.2f}%")