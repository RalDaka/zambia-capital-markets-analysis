import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="LuSE Market Analytics",
    layout="wide"
)

st.title("LuSE Market Analytics Dashboard")

st.markdown(
    "This dashboard explores historical LuSE share price data and shows how selected "
    "counters have performed over time. It is designed as a data analysis and financial "
    "literacy project, not as an investment recommendation tool."
)

# Load data
df = pd.read_csv("data/processed/luse_historical_prices_clean.csv")

# Clean data types
df["date"] = pd.to_datetime(df["date"])
df["price"] = pd.to_numeric(df["price"], errors="coerce")
df["volume"] = pd.to_numeric(df["volume"], errors="coerce")
df["daily_return"] = pd.to_numeric(df["daily_return"], errors="coerce")

# Market overview
st.subheader("Market Overview")

st.markdown(
    "The overview cards summarize the dataset by showing the number of counters "
    "included and the most recent market record available."
)

total_companies = df["ticker"].nunique()
latest_data_date = df["date"].max().strftime("%Y-%m-%d")

col1, col2 = st.columns(2)

col1.metric("Listed Companies", total_companies)
col2.metric("Latest Data Date", latest_data_date)

st.divider()

# Quick period selector
st.subheader("Select Analysis Period")

latest_date = df["date"].max()
min_date = df["date"].min()

period = st.radio(
    "Select analysis period",
    ["1M", "3M", "6M", "1Y", "YTD", "MAX"],
    horizontal=True,
    label_visibility="collapsed"
)

# Determine default start date based on quick period selection
if period == "1M":
    default_start = latest_date - pd.DateOffset(months=1)
elif period == "3M":
    default_start = latest_date - pd.DateOffset(months=3)
elif period == "6M":
    default_start = latest_date - pd.DateOffset(months=6)
elif period == "1Y":
    default_start = latest_date - pd.DateOffset(years=1)
elif period == "YTD":
    default_start = pd.Timestamp(year=latest_date.year, month=1, day=1)
else:  # MAX
    default_start = min_date

# Manual date range selector (populated by quick period selection)
col_date1, col_date2 = st.columns(2)
with col_date1:
    start_date = st.date_input("Start Date", value=default_start, min_value=min_date, max_value=latest_date)
with col_date2:
    end_date = st.date_input("End Date", value=latest_date, min_value=min_date, max_value=latest_date)

st.caption(
    "Quick period selections provide a fast way to analyze recent market performance, "
    "while manual dates allow more detailed historical analysis."
)

# Apply final date filter using the manual date inputs
filtered_df = df[
    (df["date"] >= pd.to_datetime(start_date)) &
    (df["date"] <= pd.to_datetime(end_date))
].copy()

st.divider()

# Company selector
ticker = st.selectbox(
    "Select a company",
    sorted(filtered_df["ticker"].unique())
)

company_df = filtered_df[filtered_df["ticker"] == ticker].copy()
company_df = company_df.sort_values("date")

# Handle case where ticker has no data in the selected period
if company_df.empty:
    st.warning(
        f"No data available for {ticker} in the selected period ({period}). "
        f"Try selecting a different period or ticker."
    )
else:
    # Show data range for the selected ticker
    ticker_start = company_df["date"].min().strftime("%Y-%m-%d")
    ticker_end = company_df["date"].max().strftime("%Y-%m-%d")
    st.caption(f"Showing data from {ticker_start} to {ticker_end} for {ticker}.")

    # Historical price chart
    st.subheader(f"{ticker} Historical Share Price")

    st.markdown(
        "This chart shows the selected company's historical share price movement over time. "
        "It helps users observe long-term price trends, periods of stability, and periods of "
        "sharper price movement."
    )

    fig = px.line(
        company_df,
        x="date",
        y="price",
        title=f"{ticker} Historical Share Price"
    )

    st.plotly_chart(fig, use_container_width=True)

    # Normalized performance chart
    company_df["normalized_price"] = (
        company_df["price"] / company_df["price"].iloc[0]
    )

    st.subheader(f"{ticker} Normalized Performance")

    st.markdown(
        "Normalized performance shows how the selected counter would have grown relative "
        "to its starting price. This makes it easier to understand investment growth over "
        "time, regardless of the original share price."
    )

    normalized_fig = px.line(
        company_df,
        x="date",
        y="normalized_price",
        title=f"{ticker} Normalized Growth"
    )

    st.plotly_chart(normalized_fig, use_container_width=True)

    # Key metrics
    st.subheader("Key Metrics")

    st.markdown(
        "These metrics summarize the selected counter's latest price, total return over the "
        "available period, total traded volume, and volatility. Volatility is used here as a "
        "simple measure of price movement or risk."
    )

    latest_price = company_df["price"].iloc[-1]
    first_price = company_df["price"].iloc[0]
    total_return = ((latest_price - first_price) / first_price) * 100
    total_volume = company_df["volume"].sum()
    volatility = company_df["daily_return"].std() * 100

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Latest Price", f"{latest_price:,.2f}")
    col2.metric("Total Return", f"{total_return:,.2f}%")
    col3.metric("Total Volume", f"{total_volume:,.0f}")
    col4.metric("Volatility", f"{volatility:,.2f}%")

st.divider()

# Top performing stocks
st.subheader("Top Performing Stocks")

performance_df = (
    filtered_df.sort_values("date")
    .groupby("ticker")
    .agg(
        first_price=("price", "first"),
        latest_price=("price", "last")
    )
)

performance_df["return_percent"] = (
    (performance_df["latest_price"] - performance_df["first_price"])
    / performance_df["first_price"]
) * 100

performance_df = performance_df.sort_values(
    "return_percent",
    ascending=False
)

st.markdown(
    "This table compares counters based on total return over the available dataset. "
    "It helps identify which counters had the strongest historical price growth, but "
    "past performance does not guarantee future results."
)

st.dataframe(
    performance_df[["first_price", "latest_price", "return_percent"]].head(10)
)

st.divider()

# Multi-stock normalized performance comparison
st.subheader("Multi-Stock Normalized Performance Comparison")

default_tickers = ["ZNCO", "ZCCM", "SCBL"]
selected_tickers = st.multiselect(
    "Select tickers to compare",
    options=sorted(filtered_df["ticker"].unique()),
    default=default_tickers
)

st.markdown(
    "This chart allows users to compare multiple counters on a normalized basis. Since "
    "all selected counters start from the same baseline, the chart focuses on relative "
    "growth rather than raw share price differences."
)

if selected_tickers:
    comparison_df = filtered_df[filtered_df["ticker"].isin(selected_tickers)].copy()
    comparison_df["normalized_price"] = comparison_df.groupby("ticker")["price"].transform(
        lambda x: x / x.iloc[0]
    )

    fig_comparison = px.line(
        comparison_df,
        x="date",
        y="normalized_price",
        color="ticker",
        title="Normalized Stock Performance Comparison"
    )

    st.plotly_chart(fig_comparison, use_container_width=True)
else:
    st.info("Please select at least one ticker to display the comparison chart.")

st.divider()

# Disclaimer
st.warning(
    "**Disclaimer:** This dashboard is for educational and data analysis purposes only. "
    "The information presented may contain errors, omissions, or outdated data and should "
    "not be relied upon for investment decisions. Users should verify information from "
    "official sources such as the Lusaka Securities Exchange, the Securities and Exchange "
    "Commission, licensed brokers, and other appropriate institutions. Anyone intending to "
    "invest should seek guidance from a registered investment advisor or other qualified "
    "professional."
)
