import pandas as pd
import streamlit as st


st.set_page_config(page_title="Online Retail Dashboard", page_icon=":bar_chart:", layout="wide")


@st.cache_data
def load_and_prepare_data():
    df = pd.read_excel("Online Retail.xlsx")
    df = df.drop_duplicates().dropna().copy()
    df = df[~df["InvoiceNo"].astype(str).str.startswith("C", na=False)].copy()
    df = df[(df["Quantity"] > 0) & (df["UnitPrice"] > 0)].copy()
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
    df["Revenue"] = df["Quantity"] * df["UnitPrice"]
    df["Month"] = df["InvoiceDate"].dt.to_period("M").astype(str)
    return df


def country_summary(df: pd.DataFrame) -> pd.DataFrame:
    out = (
        df.groupby("Country", as_index=False)
        .agg(Revenue=("Revenue", "sum"), Sales=("Quantity", "sum"), Orders=("InvoiceNo", "nunique"))
        .sort_values("Revenue", ascending=False)
    )
    out["AOV"] = out["Revenue"] / out["Orders"]
    return out


def product_summary(df: pd.DataFrame) -> pd.DataFrame:
    out = (
        df.groupby(["StockCode", "Description"], as_index=False)
        .agg(Revenue=("Revenue", "sum"), Quantity=("Quantity", "sum"), Orders=("InvoiceNo", "nunique"))
        .sort_values("Revenue", ascending=False)
    )
    return out


df = load_and_prepare_data()
total_revenue = df["Revenue"].sum()
total_customers = df["CustomerID"].nunique()
total_orders = df["InvoiceNo"].nunique()
aov = total_revenue / total_orders if total_orders else 0
return_rate = (df["Quantity"] <= 0).mean() * 100

monthly = (
    df.groupby("Month", as_index=False)
    .agg(Revenue=("Revenue", "sum"), Orders=("InvoiceNo", "nunique"), Quantity=("Quantity", "sum"))
    .sort_values("Month")
)
countries = country_summary(df)
products = product_summary(df)

st.title("Online Retail - Business Overview")
st.caption("Built from cleaned transaction data used in your notebook analysis.")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Revenue", f"{total_revenue:,.2f}")
col2.metric("Customers", f"{int(total_customers):,}")
col3.metric("Average Order Value", f"{aov:,.2f}")
col4.metric("Return/Negative Qty Rate", f"{return_rate:.2f}%")

st.subheader("Revenue Trends")
trend_col1, trend_col2 = st.columns(2)
trend_col1.line_chart(monthly.set_index("Month")[["Revenue"]], use_container_width=True)
trend_col2.line_chart(monthly.set_index("Month")[["Orders"]], use_container_width=True)

st.subheader("Geographic Analysis")
geo_left, geo_right = st.columns([2, 1])
geo_left.dataframe(
    countries.head(15).style.format({"Revenue": "{:,.2f}", "Sales": "{:,.0f}", "Orders": "{:,.0f}", "AOV": "{:,.2f}"}),
    use_container_width=True,
)
geo_right.bar_chart(countries.head(10).set_index("Country")["Revenue"], use_container_width=True)

st.subheader("Product Performance")
prod_left, prod_right = st.columns(2)
prod_left.dataframe(
    products.head(15).style.format({"Revenue": "{:,.2f}", "Quantity": "{:,.0f}", "Orders": "{:,.0f}"}),
    use_container_width=True,
)
top10 = products.head(10).copy()
top10["Product"] = top10["Description"].str.slice(0, 40)
prod_right.bar_chart(top10.set_index("Product")["Revenue"], use_container_width=True)

