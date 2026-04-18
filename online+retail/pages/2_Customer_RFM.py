from pathlib import Path

import pandas as pd
import streamlit as st


st.set_page_config(page_title="Customer RFM", page_icon=":busts_in_silhouette:", layout="wide")

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR.parent / "Online Retail.xlsx"


@st.cache_data
def load_clean_data():
    if not DATA_PATH.exists():
        st.error(f"Dataset not found: {DATA_PATH}")
        st.stop()

    df = pd.read_excel(DATA_PATH)
    df = df.drop_duplicates().dropna().copy()
    df = df[~df["InvoiceNo"].astype(str).str.startswith("C", na=False)].copy()
    df = df[(df["Quantity"] > 0) & (df["UnitPrice"] > 0)].copy()
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
    df["Revenue"] = df["Quantity"] * df["UnitPrice"]
    return df


@st.cache_data
def build_rfm(df: pd.DataFrame):
    snapshot_date = df["InvoiceDate"].max() + pd.Timedelta(days=1)
    rfm = (
        df.groupby("CustomerID")
        .agg(
            Recency=("InvoiceDate", lambda x: (snapshot_date - x.max()).days),
            Frequency=("InvoiceNo", "nunique"),
            Monetary=("Revenue", "sum"),
        )
        .reset_index()
    )

    rfm["R_Score"] = pd.qcut(rfm["Recency"], q=5, labels=[5, 4, 3, 2, 1], duplicates="drop").astype(int)
    rfm["F_Score"] = pd.qcut(
        rfm["Frequency"].rank(method="first"), q=5, labels=[1, 2, 3, 4, 5], duplicates="drop"
    ).astype(int)
    rfm["M_Score"] = pd.qcut(
        rfm["Monetary"].rank(method="first"), q=5, labels=[1, 2, 3, 4, 5], duplicates="drop"
    ).astype(int)

    def segment_customer(row):
        r, f = row["R_Score"], row["F_Score"]
        if r >= 4 and f >= 4:
            return "Champions"
        if r >= 3 and f >= 4:
            return "Loyal Customers"
        if r >= 4 and f >= 2:
            return "Potential Loyalists"
        if r == 5 and f == 1:
            return "New Customers"
        if r == 4 and f == 1:
            return "Promising"
        if r == 3 and f <= 2:
            return "Need Attention"
        if r <= 2 and f >= 3:
            return "At Risk"
        if r <= 2 and f <= 2:
            return "Lost"
        return "Others"

    rfm["Segment"] = rfm.apply(segment_customer, axis=1)
    return rfm


def recommendation_for_segment(segment: str) -> str:
    recs = {
        "Champions": "Keep engaged with VIP perks, early access products, and personalized thank-you campaigns.",
        "Loyal Customers": "Nudge toward higher basket size with bundles and category-based cross-sell recommendations.",
        "Potential Loyalists": "Drive repeat purchases using limited-time incentives and post-purchase reminders.",
        "New Customers": "Onboard with welcome offers and product discovery flows to secure a second purchase quickly.",
        "Promising": "Send targeted promotions to build purchase frequency while interest is still fresh.",
        "Need Attention": "Re-engage with value-driven messaging and personalized product picks.",
        "At Risk": "Run win-back campaigns with stronger incentives and reminders tied to previous purchases.",
        "Lost": "Use low-cost reactivation campaigns and suppress users with repeated non-response.",
        "Others": "Test segmented messaging to determine engagement drivers.",
    }
    return recs.get(segment, recs["Others"])


df = load_clean_data()
rfm = build_rfm(df)

st.title("Customer RFM Analysis")
st.caption("Lookup individual customers and review segment-level recommendations.")

customer_ids = sorted(rfm["CustomerID"].unique())
selected_customer = st.selectbox("Select CustomerID", options=customer_ids, format_func=lambda x: f"{int(x)}")

customer_rfm = rfm[rfm["CustomerID"] == selected_customer].iloc[0]
customer_txn = df[df["CustomerID"] == selected_customer].copy()

segment = customer_rfm["Segment"]

st.markdown(
    f"""
    <div style="padding: 14px; border: 1px solid #334155; border-radius: 10px; background-color: #0f172a;">
        <h4 style="margin: 0 0 6px 0; color: #ffffff;">Segment: {segment}</h4>
        <p style="margin: 0; color: #cbd5e1;">{recommendation_for_segment(segment)}</p>
    </div>
    """,
    unsafe_allow_html=True,
)

first_purchase = customer_txn["InvoiceDate"].min()
last_purchase = customer_txn["InvoiceDate"].max()
txn_count = customer_txn["InvoiceNo"].nunique()
cust_revenue = customer_txn["Revenue"].sum()
cust_aov = cust_revenue / txn_count if txn_count else 0
country = customer_txn["Country"].mode().iat[0] if not customer_txn["Country"].mode().empty else "Unknown"

st.subheader("Customer Profile")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Country", country)
c2.metric("Transactions", f"{txn_count:,}")
c3.metric("Total Revenue", f"{cust_revenue:,.2f}")
c4.metric("Customer AOV", f"{cust_aov:,.2f}")
c5.metric("Recency (days)", f"{int(customer_rfm['Recency'])}")

date_col1, date_col2 = st.columns(2)
date_col1.info(f"First Purchase: {first_purchase.date()}")
date_col2.info(f"Last Purchase: {last_purchase.date()}")

st.subheader("Top Products Purchased")
prod = (
    customer_txn.groupby("Description", as_index=False)
    .agg(Revenue=("Revenue", "sum"), Quantity=("Quantity", "sum"))
    .sort_values("Revenue", ascending=False)
    .head(10)
)
st.bar_chart(prod.set_index("Description")["Revenue"], use_container_width=True)

st.subheader("Product Categories Purchased")
desc = customer_txn["Description"].astype(str).str.upper()
category_map = [
    ("Storage & Containers", r"JAR|TIN|BOX|DRAWER|BASKET|BAG|STORAGE|HOLDER|ORGANISER|ORGANIZER"),
    ("Home Decor & Lighting", r"LAMP|LIGHT|LANTERN|CANDLE|ORNAMENT|HEART|DECORATION|FRAME|MIRROR"),
    ("Kitchen & Dining", r"MUG|CUP|BOWL|PLATE|DISH|SPOON|KNIFE|TEAPOT|CAKESTAND|GLASS|JUG|TRAY"),
    ("Stationery & Crafts", r"PAPER|CARD|STICKER|NOTEBOOK|PENCIL|PEN|CRAFT|ENVELOPE|WRAP"),
    ("Kids & Toys", r"TOY|DOLL|RABBIT|CHILD|KIDS|GLIDER|GAME|PUZZLE"),
]

cust_cat = pd.Series("Other", index=customer_txn.index)
for name, pattern in category_map:
    mask = desc.str.contains(pattern, regex=True, na=False)
    cust_cat.loc[mask] = name

cat_summary = (
    customer_txn.assign(Category=cust_cat)
    .groupby("Category", as_index=False)
    .agg(Revenue=("Revenue", "sum"))
    .sort_values("Revenue", ascending=False)
)
st.bar_chart(cat_summary.set_index("Category")["Revenue"], use_container_width=True)
