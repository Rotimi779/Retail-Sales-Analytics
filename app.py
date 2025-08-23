import os
import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ─────────────────────────────
# App & Paths
# ─────────────────────────────
st.set_page_config(page_title="Data Analysis Dashboard", layout="wide")

DB_PATH = "retail_sales.db"
CSV_DIR = "csv_files"

TABLES = ["customers", "inventory", "products", "sales", "stores"]

# Caching functions
@st.cache_resource
def get_conn(db_path: str = DB_PATH):
    # one shared connection per session
    return sqlite3.connect(db_path, check_same_thread=False)

@st.cache_data(ttl=300)
def load_sql(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

@st.cache_data(ttl=300)
def run_query(sql: str, params: tuple | None = None) -> pd.DataFrame:
    # cached returned DataFrames; params become cache key
    conn = get_conn()
    return pd.read_sql_query(sql, conn, params=params)

@st.cache_data(ttl=300)
def read_csv_table(name: str) -> pd.DataFrame:
    return pd.read_csv(os.path.join(CSV_DIR, f"{name}.csv"))

def _csv_signature() -> tuple:
    """Lightweight signature so cache/refresh decision can be made (mtime,size)."""
    sig = []
    for t in TABLES:
        p = os.path.join(CSV_DIR, f"{t}.csv")
        stat = os.stat(p)
        sig.append((t, stat.st_mtime, stat.st_size))
    return tuple(sig)

@st.cache_data(show_spinner=False)
def build_database_if_needed(sig: tuple):
    """
    Rebuild tables from CSVs into SQLite.
    This function is cached keyed by the CSV signature. If CSVs don't change,
    this won't run again.
    """
    conn = get_conn()
    for name in TABLES:
        df = read_csv_table(name)

        # date conversions for sales & inventory
        if name in ["sales", "inventory"]:
            if "last_updated" in df.columns:
                df["last_updated"] = pd.to_datetime(df["last_updated"], errors="coerce").dt.date
            if "sale_date" in df.columns:
                df["sale_date"] = pd.to_datetime(df["sale_date"], errors="coerce").dt.date

        df.to_sql(name, conn, if_exists="replace", index=False)
    return "ok"

# Controls to rebuild / refresh
left, right = st.columns([1, 3])
with left:
    if st.button("🔄 Rebuild database from CSVs"):
        st.cache_data.clear()  # clear caches so the next call rebuilds
        build_database_if_needed.clear()  # clear build cache specifically



masking_dict = {"total_revenue": "Revenue", "total_orders":"Orders", "units_sold": "Units Sold", "average_order_value":"Average Order Value"}
#Key Performance Indicator Graphing
def make_kpi_line(df: pd.DataFrame, value_col: str, use_moving_average: bool):
    display_name = masking_dict.get(value_col, value_col)
    d = df[["month_year", value_col]].copy()
    d["month_year"] = pd.to_datetime(d["month_year"]) + pd.offsets.MonthEnd(0)

    # Optional 3-month moving average
    ma_col = f"{value_col}_ma3"
    if use_moving_average:
        d[ma_col] = d[value_col].rolling(3).mean()

    fig = px.line(
        d,
        x="month_year",
        y=value_col,
        markers=True,
        title=display_name,
        labels={"month_year": "Month", value_col: display_name},
    )
    if use_moving_average:
        fig.add_scatter(x=d["month_year"], y=d[ma_col], mode="lines", name="3-mo avg")

    # annotations
    peak = d.loc[d[value_col].idxmax()]
    low = d.loc[d[value_col].idxmin()]

    is_currency = value_col in {"total_revenue", "average_order_value"}
    y_prefix = "$" if is_currency else ""
    hover_val_fmt = "$%{y:,.0f}" if is_currency else "%{y:,.0f}"

    fig.add_annotation(x=peak["month_year"], y=peak[value_col],
                       text=f"Peak: {y_prefix}{peak[value_col]:,.0f}",
                       showarrow=True, arrowhead=2, yshift=10)
    fig.add_annotation(x=low["month_year"], y=low[value_col],
                       text=f"Low: {y_prefix}{low[value_col]:,.0f}",
                       showarrow=True, arrowhead=2, yshift=-10)

    fig.update_traces(hovertemplate=f"%{{x|%b %Y}}<br>{display_name}: {hover_val_fmt}")
    fig.update_layout(
        template="plotly_white",
        hovermode="x unified",
        margin=dict(l=10, r=10, t=100, b=70),
        yaxis_tickprefix=y_prefix,
        yaxis_separatethousands=True,
        legend_title_text="",
    )
    fig.update_xaxes(
        rangeslider_visible=True,
        rangeselector=dict(buttons=[
            dict(count=3, step="month", stepmode="backward", label="3M"),
            dict(count=6, step="month", stepmode="backward", label="6M"),
            dict(count=9, step="month", stepmode="backward", label="9M"),
            dict(step="all", label="All"),
        ])
    )
    return fig

def make_store_trend_fig(df: pd.DataFrame, value_col: str, months_back: int | None = None, title: str | None = None):
    if df.empty or value_col not in df.columns:
        raise ValueError("Dataframe is empty or value_col not present.")
    d = df[["month_year", value_col]].copy()
    d["month_year"] = pd.to_datetime(d["month_year"]) + pd.offsets.MonthEnd(0)
    d = d.sort_values("month_year").reset_index(drop=True)
    if months_back is not None and months_back > 0:
        d = d.iloc[-months_back:].copy()
    display_name = masking_dict.get(value_col, value_col)
    is_currency = value_col in {"total_revenue", "average_order_value"}
    y_prefix = "$" if is_currency else ""
    hover_val_fmt = "$%{y:,.0f}" if is_currency else "%{y:,.0f}"
    fig = px.line(
        d, x="month_year", y=value_col, markers=True,
        title=title or f"{display_name} Trend",
        labels={"month_year": "Month", value_col: display_name},
    )
    peak = d.loc[d[value_col].idxmax()]
    low = d.loc[d[value_col].idxmin()]
    fig.add_annotation(x=peak["month_year"], y=peak[value_col],
                       text=f"Peak: {y_prefix}{peak[value_col]:,.0f}",
                       showarrow=True, arrowhead=2, yshift=10)
    fig.add_annotation(x=low["month_year"], y=low[value_col],
                       text=f"Low: {y_prefix}{low[value_col]:,.0f}",
                       showarrow=True, arrowhead=2, yshift=-10)
    fig.update_traces(hovertemplate=f"%{{x|%b %Y}}<br>{display_name}: {hover_val_fmt}")
    fig.update_layout(
        template="plotly_white",
        hovermode="x unified",
        margin=dict(l=10, r=10, t=80, b=10),
        yaxis_tickprefix=y_prefix,
        yaxis_separatethousands=True,
        legend_title_text="",
    )
    return fig

def make_pareto_chart(df: pd.DataFrame, category_col: str = "category", value_col: str = "revenue", cutoff: float = 0.80, title: str = "Pareto: Revenue by Category"):
    d = df[[category_col, value_col]].dropna().copy()
    d = d.groupby(category_col, as_index=False)[value_col].sum()

    # Sort descending and compute cumulative %
    d = d.sort_values(value_col, ascending=False).reset_index(drop=True)
    total = d[value_col].sum()
    d["cum_value"] = d[value_col].cumsum()
    d["cum_pct"] = d["cum_value"] / (total if total else 1)

    # Find cutoff index (first row where cum_pct >= cutoff)
    cutoff_idx = int((d["cum_pct"] >= cutoff).idxmax()) if len(d) else 0
    top_k = cutoff_idx + 1 if len(d) else 0
    pct_at_cutoff = float(d.loc[cutoff_idx, "cum_pct"]) if len(d) else 0.0
    top_labels = d.loc[:cutoff_idx, category_col].tolist() if len(d) else []

    # Build figure (bars + cumulative line on secondary y-axis)
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Bar(
            x=d[category_col],
            y=d[value_col],
            name="Value",
            hovertemplate=f"%{{x}}<br>{value_col}: $%{{y:,.0f}}<extra></extra>"
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=d[category_col],
            y=(d["cum_pct"] * 100),
            mode="lines+markers",
            name="Cumulative %",
            hovertemplate="%{x}<br>Cumulative: %{y:.1f}%<extra></extra>"
        ),
        secondary_y=True,
    )

    # 80% horizontal line
    fig.add_hline(y=cutoff * 100, line_dash="dash", line_color="gray",
                  annotation_text=f"{int(cutoff*100)}% target", annotation_position="top left",
                  secondary_y=True)

    # Vertical line at cutoff category
    if len(d):
        fig.add_vline(x=cutoff_idx, line_dash="dot", line_color="gray",
                      annotation_text=f"Top {top_k} categories", annotation_position="top")

    # Layout
    fig.update_layout(
        title=dict(text=title, x=0.5, xanchor="center", yanchor="top", pad=dict(t=20)),
        template="plotly_white",
        margin=dict(l=10, r=10, t=80, b=10),
        hovermode="x unified",
        legend_title_text="",
    )
    fig.update_yaxes(
        title_text="Revenue",
        tickprefix="$",
        separatethousands=True,
        secondary_y=False,
    )
    fig.update_yaxes(
        title_text="Cumulative %",
        range=[0, 100],
        ticksuffix="%",
        secondary_y=True,
    )

    return fig, {"top_k": top_k, "pct": pct_at_cutoff, "top_labels": top_labels}



# always ensure DB is in sync with CSVs (cached by signature)
status = build_database_if_needed(_csv_signature())

st.title("Data Analysis Dashboard")


# Main KPIs (use cached run_query)
st.header("Monthly Key Performance Indicators")

st.info(
    """
    Track key performance trends over time:  
    - **Revenue:** Total monthly sales revenue.  
    - **Total Orders:** Number of customer purchases.  
    - **Units Sold:** Quantity of products sold.  
    - **Average Order Value (AOV):** Revenue per order.  

    Use the tabs to switch between metrics and monitor growth, seasonality, and shifts in customer behavior.
    """
)
tab1, tab2, tab3, tab4 = st.tabs(["Revenue", "Total Orders", "Units sold", "Average Order Value"])


kpi_df = run_query(load_sql("queries/main_kpi_summary.txt"))

with tab1:
    st.plotly_chart(make_kpi_line(kpi_df, "total_revenue", use_moving_average=True), use_container_width=True)
with tab2:
    st.plotly_chart(make_kpi_line(kpi_df, "total_orders", use_moving_average=False), use_container_width=True)
with tab3:
    st.plotly_chart(make_kpi_line(kpi_df, "units_sold", use_moving_average=False), use_container_width=True)
with tab4:
    st.plotly_chart(make_kpi_line(kpi_df, "average_order_value", use_moving_average=False), use_container_width=True)

st.markdown("<br><br>", unsafe_allow_html=True)

# Category and Region Insights tab
st.header("Category and Region Insights")
st.info(
    """
    Explore where revenue comes from:
    - **Categories (Pareto):** See which categories drive ~80% of revenue.
    - **Region & Category Mix:** Treemap of category performance within each region.
    - **Regional Breakdown:** Stacked bars showing which regions make the most and what drives them.
    """
)

tab_cat, tab_mix, tab_reg = st.tabs(["Categories (Pareto)", "Region & Category Mix", "Regional Breakdown"])

# Pareto chart
with tab_cat:
    cat_reg_df = run_query(load_sql("queries/top_category.txt"))
    pareto_fig, info = make_pareto_chart(cat_reg_df, "category", "total_revenue", cutoff=0.80, title="")
    st.plotly_chart(pareto_fig, use_container_width=True)
    pct_str = f"{info['pct']*100:.0f}%"
    st.info(f"Top {info['top_k']} categories make up {pct_str} of revenue: {', '.join(info['top_labels'])}.")

# Treemap diagram
with tab_mix:
    rc_df = run_query(load_sql("queries/region_category_heatmap.txt"))
    fig_tree = px.treemap(rc_df, path=["region", "category"], values="total_revenue",
                          title="Revenue by Region and Category")
    fig_tree.update_traces(hovertemplate="Path: %{label}<br>Revenue: $%{value:,.0f}<extra></extra>")
    fig_tree.update_layout(template="plotly_white", margin=dict(l=10, r=10, t=80, b=10),
                           title=dict(x=0.5, xanchor="center", yanchor="top", pad=dict(t=20)))
    st.plotly_chart(fig_tree, use_container_width=True)

# Stacked bars for category and revenue
with tab_reg:
    if 'rc_df' not in locals():
        rc_df = run_query(load_sql("queries/region_category_heatmap.txt"))

    region_totals = rc_df.groupby("region", as_index=False)["total_revenue"].sum()
    region_order = region_totals.sort_values("total_revenue", ascending=False)["region"].tolist()

    fig_stack = px.bar(rc_df, x="region", y="total_revenue", color="category",
                       title="Which Regions Make the Most (and What’s Driving It)")
    fig_stack.update_traces(hovertemplate="%{x}<br>%{fullData.name}: $%{y:,.0f}<extra></extra>")
    fig_stack.update_layout(barmode="stack", template="plotly_white",
                            margin=dict(l=10, r=10, t=80, b=10),
                            title=dict(x=0.5, xanchor="center", yanchor="top", pad=dict(t=20)),
                            legend_title_text="Category")
    fig_stack.update_xaxes(categoryorder="array", categoryarray=region_order)
    fig_stack.update_yaxes(tickprefix="$", separatethousands=True, title_text="Revenue")
    st.plotly_chart(fig_stack, use_container_width=True)

    # Insight
    top_region_row = region_totals.loc[region_totals["total_revenue"].idxmax()]
    top_region, top_region_revenue = top_region_row["region"], top_region_row["total_revenue"]
    top_cat_row = (rc_df[rc_df["region"] == top_region]
                   .groupby("category", as_index=False)["total_revenue"].sum()
                   .sort_values("total_revenue", ascending=False).iloc[0])
    st.info(
        f"{top_region} leads with ${top_region_revenue:,.0f}. "
        f"Within {top_region}, {top_cat_row['category']} contributes {top_cat_row['total_revenue']:,.0f}."
    )

st.markdown("<br><br>", unsafe_allow_html=True)




# Store performance (queries now cached)
st.header("Store Performance")
st.info(
    """
    This section provides a breakdown of store-level performance.  
    - On the **left**, you can view a summary table for all stores.  
    - On the **right**, select a store to explore detailed **KPI trends** (revenue, orders, units, AOV)  
      and **product/category performance**.  
    - Use the dropdowns to change the time period or metric.  
    """
)

col1, col2 = st.columns([1, 2])

all_store_df = run_query(load_sql("queries/all_stores_performance.txt"))
with col1:
    st.dataframe(all_store_df)
    #orst.dataframe(all_store_df, use_container_width=True, height=all_store_df.shape[0]*35)

with col2:
    st.write("**Select which store you want to look at.**")
    selected_store = st.selectbox("Choose a store", options=all_store_df["store_name"].tolist())

    kpi_tab, products_tab = st.tabs(["KPI Trends", "Top Products"])

    with kpi_tab:
        kpi_store_df = run_query(load_sql("queries/store_kpi_summary.txt"), params=(selected_store,))
        if not kpi_store_df.empty:
            month_options = {f"Last {i} months": i for i in range(12, 1, -1)}
            month_options["Last month"] = 1
            month_options["All time"] = None
            selected_label = st.selectbox("Select period", list(month_options.keys()))
            months_back = month_options[selected_label]

            plot_df = kpi_store_df if months_back is None else kpi_store_df.iloc[-months_back:]

            total_rev = plot_df["total_revenue"].sum()
            total_orders = plot_df["total_orders"].sum()
            total_units = plot_df["units_sold"].sum()
            aov_weighted = (total_rev / total_orders) if total_orders else 0.0

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Revenue", f"${total_rev:,.0f}")
            c2.metric("Orders", f"{int(total_orders):,}")
            c3.metric("Units", f"{int(total_units):,}")
            c4.metric("AOV", f"${aov_weighted:,.0f}")

            metric_map = {
                "Revenue": "total_revenue",
                "Orders": "total_orders",
                "Units Sold": "units_sold",
                "Average Order Value": "average_order_value",
            }
            chosen_metric_label = st.selectbox("Trend metric", list(metric_map.keys()))
            chosen_col = metric_map[chosen_metric_label]

            fig = make_store_trend_fig(
                df=kpi_store_df,
                value_col=chosen_col,
                months_back=months_back,
                title=f"{chosen_metric_label} — {selected_store} ({selected_label})",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data for this store yet.")

    with products_tab:
        option_select = st.selectbox("Select a chart to view", options=["Top Categories", "Top Products"])
        if option_select == "Top Categories":
            cat_df = run_query(load_sql("queries/all_stores_category.txt"), params=(selected_store,))
            if not cat_df.empty:
                cat_df = cat_df.sort_values("revenue", ascending=True)
                total_rev = cat_df["revenue"].sum()
                cat_df["share"] = (cat_df["revenue"] / total_rev).fillna(0)
                fig_cat = px.bar(
                    cat_df, x="revenue", y="category", orientation="h",
                    title=f"Top Categories by Revenue — {selected_store}",
                    labels={"revenue": "Revenue", "category": "Category"},
                    text=cat_df["share"].map(lambda x: f"{x*100:.0f}%"),
                )
                fig_cat.update_traces(
                    hovertemplate="%{y}<br>Revenue: $%{x:,.0f}<br>Share: %{text}<extra></extra>",
                    textposition="outside", cliponaxis=False,
                )
                fig_cat.update_layout(
                    template="plotly_white", margin=dict(l=10, r=10, t=80, b=10),
                    hovermode="y unified", xaxis_title="Revenue", yaxis_title="Category",
                )
                fig_cat.update_xaxes(tickprefix="$", separatethousands=True)
                st.plotly_chart(fig_cat, use_container_width=True)

                top_row = cat_df.sort_values("revenue", ascending=False).iloc[0]
                st.caption(f"{top_row['category']} leads this store with "
                           f"${top_row['revenue']:,.0f} ({top_row['share']*100:.0f}% of category revenue).")
            else:
                st.info("No category revenue found for this store.")

        if option_select == "Top Products":
            prod_df = run_query(load_sql("queries/all_stores_products.txt"), params=(selected_store,))
            if not prod_df.empty:
                prod_df = prod_df.sort_values("revenue", ascending=True)
                fig_top = px.bar(
                    prod_df, x="revenue", y="product_name", orientation="h",
                    title=f"Top Products by Revenue — {selected_store}",
                    labels={"revenue": "Revenue", "product_name": "Product"},
                )
                fig_top.update_layout(template="plotly_white",
                                      margin=dict(l=10, r=10, t=80, b=10),
                                      hovermode="y unified")
                fig_top.update_xaxes(tickprefix="$", separatethousands=True)
                st.plotly_chart(fig_top, use_container_width=True)

                total_rev = prod_df["revenue"].sum()
                top3 = prod_df.sort_values("revenue", ascending=False).head(3)
                share = top3["revenue"].sum() / total_rev if total_rev else 0
                st.caption(f"Top 3 products contribute {share*100:.0f}% of store revenue.")
            else:
                st.info("No product sales found for this store.")


st.markdown("<br><br>", unsafe_allow_html=True)

# Inventory Tab
st.header("Inventory Check")
st.info(
    "This tab helps you identify **stock risks** and operational signals:\n\n"
    "- **Low-Stock Risk Table**: Highlights products at risk of stockouts, based on either:\n"
    "  bottom X% of stock within their category (percentile rule), or\n"
    "  stock coverage below the critical threshold in months (coverage rule).\n"
    "- **Category Stock Levels Chart**: Compares average stock vs. average monthly sales per category.\n"
    "- Use the sliders and filters above the table to adjust the cutoff and focus on categories of interest.\n"
    "- You can also download the current risk table as CSV for further analysis.\n"
    "- Use the slider and filter above the **Category Stock Level Chart** to adjust the critical coverage threshold and to view the top categories."
)


#Low stock risk table section
st.subheader("Low Stock Risk")
low_stock_df = run_query(load_sql("queries/inventory_tab_low_stock_risk.txt"))
if low_stock_df.empty:
        st.info("No inventory data available.")
c1, c2, c3 = st.columns([1, 1, 1])
with c1:
    # Percentile to flag "at-risk" (default bottom 15%)
    pct = st.slider("Risk cutoff (bottom % by category)", min_value=5, max_value=50, value=15, step=5)
with c2:
    # (optional)
    categories = sorted(low_stock_df["category"].dropna().unique().tolist())
    pick_cats = st.multiselect("Filter categories", categories, default=categories)
with c3:
    # Coverage threshold (months)
    cov_threshold = st.number_input("Critical coverage (months)", min_value=0.0, value=1.0, step=0.5)

# Filter by category selection
d = low_stock_df[low_stock_df["category"].isin(pick_cats)].copy()
d["risk_percentile"] = (d.groupby("category")["avg_stock"].rank(method="min", pct=True))

# Flag low coverage (<= threshold) OR bottom X% by stock within category
cutoff = pct / 100.0

flag_percentile = d["risk_percentile"] <= cutoff
flag_coverage = d["stock_coverage"].fillna(0) <= cov_threshold

# Risk reason column
d["Risk Reason"] = None
d.loc[flag_percentile & ~flag_coverage, "Risk Reason"] = "Percentile"
d.loc[~flag_percentile & flag_coverage, "Risk Reason"] = "Coverage"
d.loc[flag_percentile & flag_coverage, "Risk Reason"] = "Both"

# Keep only risky SKUs
at_risk = d[flag_percentile | flag_coverage].copy()

at_risk = at_risk.sort_values(["category", "risk_percentile", "stock_coverage"]).reset_index(drop=True)
view = at_risk.rename(columns={
"product_name": "Product",
"category": "Category",
"avg_stock": "Avg Stock",
"avg_monthly_sales": "Avg Monthly Sales",
"stock_coverage": "Stock Coverage (months)",
"risk_percentile": "Risk Percentile",
})

# Cap the percentile to [0,1] in case of outliers
view["Risk Percentile"] = view["Risk Percentile"].clip(0, 1)

# KPI: % of SKUs at risk
total_skus = len(d)
at_risk_count = len(view)
at_risk_pct = (at_risk_count / total_skus * 100) if total_skus else 0

k1, k2, k3 = st.columns(3)
k1.metric("SKUs at risk", f"{at_risk_count:,}")
k2.metric("Share of SKUs", f"{at_risk_pct:.0f}%")
k3.metric("Coverage threshold", f"{cov_threshold:.1f} mo")

st.dataframe(
        view,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Avg Stock": st.column_config.NumberColumn(format="%.0f"),
            "Avg Monthly Sales": st.column_config.NumberColumn(format="%.1f"),
            "Stock Coverage (months)": st.column_config.NumberColumn(format="%.2f"),
            "Risk Percentile": st.column_config.ProgressColumn(
                "Risk Percentile (by category)",
                help="Lower percentile = lower stock vs peers (more risky).",
                min_value=0.0, max_value=1.0
            ),
        },
    )

# Download current filtered table
csv = view.to_csv(index=False).encode("utf-8")
st.download_button(
    "⬇️ Download risk table (CSV)",
    data=csv,
    file_name="low_stock_risk.csv",
    mime="text/csv",
    use_container_width=True,
)

# Find which category concentrates most of the risk (by count)
if not view.empty:
    top_cat = (
        view.groupby("Category").size().sort_values(ascending=False).index[0])
    st.info(
        f"{at_risk_pct:.0f}% of SKUs are below critical stock levels "
        f"(≤ {cov_threshold:.1f} months coverage or bottom {pct}% by stock), "
        f"with most risk concentrated in “{top_cat}”."
    )
else:
    st.info(
        f"No SKUs currently flagged at ≤ {cov_threshold:.1f} months coverage "
        f"or bottom {pct}% by stock in the selected categories."
    )


#Category stock levels section
st.subheader("Category Stock Levels")
cat_levels_df = run_query(load_sql("queries/inventory_category_stock_levels.txt"))

if cat_levels_df.empty:
    st.info("No inventory/sales data to plot.")
else:
    # Coverage = months of stock on hand
    cat_levels_df = cat_levels_df.copy()
    cat_levels_df["coverage"] = (
        cat_levels_df["avg_stock"] / cat_levels_df["avg_monthly_sales"].replace(0, pd.NA)
    ).fillna(pd.NA)

    # Controls
    c1, c2 = st.columns([1, 1])
    with c1:
        cov_threshold = st.number_input("Critical coverage threshold (months)", min_value=0.0, value=1.0, step=0.5)
    with c2:
        show_top = st.slider("Show top N categories by coverage", 3, len(cat_levels_df), len(cat_levels_df))

    # Sort & slice
    plot_cov = cat_levels_df.sort_values("coverage", ascending=False).head(show_top)

    # Risk band label (for color)
    def band(v, thr):
        if pd.isna(v): return "No sales data"
        if v < thr:    return f"< {thr} mo (risk)"
        return f"≥ {thr} mo"

    plot_cov["risk_band"] = plot_cov["coverage"].apply(lambda v: band(v, cov_threshold))

    # Bar chart
    fig_cov = px.bar(
        plot_cov,
        x="category",
        y="coverage",
        color="risk_band",
        text=plot_cov["coverage"].map(lambda x: f"{x:.1f}" if pd.notna(x) else "—"),
        title="Stock Coverage by Category (months)",
        labels={"category": "Category", "coverage": "Coverage (months)", "risk_band": "Status"},
    )
    fig_cov.update_traces(textposition="outside", cliponaxis=False)
    fig_cov.update_layout(
        template="plotly_white",
        margin=dict(l=10, r=10, t=80, b=10),
        hovermode="x",
    )
    # Reference line at threshold
    fig_cov.add_hline(y=cov_threshold, line_dash="dot", annotation_text=f"Threshold = {cov_threshold:.1f} mo")

    st.plotly_chart(fig_cov, use_container_width=True)

    # Quick insight
    below = plot_cov["coverage"].dropna().lt(cov_threshold).mean() * 100 if not plot_cov.empty else 0
    st.caption(f"{below:.0f}% of shown categories are below the {cov_threshold:.1f}-month coverage threshold.")

    # Optional: download current view
    dl = plot_cov[["category", "avg_stock", "avg_monthly_sales", "coverage", "sku_count", "risk_band"]]
    st.download_button(
        "⬇️ Download coverage table (CSV)",
        data=dl.to_csv(index=False).encode("utf-8"),
        file_name="category_coverage.csv",
        mime="text/csv",
        use_container_width=True,
    )





#Customers Tab
st.header("Customers Analysis")
st.info(
    """
    Explore customer value and retention:

    - **Top customers (by revenue):** Use *Top customers* and *Filter categories* to aggregate spend across the selected
      categories. The **table (left)** lists each customer once with total revenue and their categories; the **bar chart (right)**
      mirrors the table. Hover to see category breakdowns and revenue.

    - **Cohort retention checkpoints:** Each cohort shows a group of customers who bought an item for the very first time in any store. The bar chart shows 
      their first month buying it, and the percentage of returning customers in subsequent months.

    - **Engagement segments:** Customers are grouped as **New (1 order month)**, **Repeat (2–4 order months)**, and **Loyal (5+ order months)**.
      The table shows revenue, customer counts, average order months, and revenue share (downloadable as CSV).
    """
)

cust_tab, = st.tabs(["Retention & Behavior"])
with cust_tab:
    customer_df = run_query(load_sql("queries/customer_order_data.txt"))
    if customer_df.empty:
        st.info("No customer transactions available.")
    else:
        
        #Cohort Retention Logic starts here
        tx = customer_df.copy()
        tx["order_month"] = pd.to_datetime(tx["order_month"])
        #Get the first month of each customer's orders
        first_month = tx.groupby("customer_id")["order_month"].min().rename("cohort_month")
        #Merge back so every customer has a known first month
        tx = tx.merge(first_month, on="customer_id", how="left")
        def month_diff(a, b):
            return (a.year - b.year) * 12 + (a.month - b.month)
        #Get how many month since the first purchase that a transaction happened.
        tx["period_number"] = tx.apply(lambda r: month_diff(r["order_month"], r["cohort_month"]), axis=1)

        #Checks each cohort's first size(number of customers) at the time the period number is 0
        cohort_sizes = (
        tx[tx["period_number"] == 0]
        .groupby("cohort_month")["customer_id"].nunique()
        .rename("cohort_size")
        )   

        #Checks how many customers were active in each cohort at each period number
        cohort_pivot = (tx.groupby(["cohort_month", "period_number"])["customer_id"].nunique().reset_index().pivot(index="cohort_month", columns="period_number", values="customer_id").fillna(0))

        #Gets the % of customers still active.
        cohort_retention = (cohort_pivot.T / cohort_sizes).T.fillna(0)
        
        #Cohort Retention Logic ends here

        #Repeat Purchase Rate logic starts here
        cust_order_counts = tx.groupby("customer_id")["order_month"].nunique().rename("order_months_count")
        total_customers = cust_order_counts.shape[0]
        repeat_customers = int((cust_order_counts >= 2).sum())
        repeat_rate = (repeat_customers / total_customers * 100) if total_customers else 0
   
        #Repeat Purchase Rate logic ends here

        
        #Customer segmentation logic starts here
        
        #To separate each customer based on the amount of orders.
        def seg(n):
            if n == 1: return "New (1 order month)"
            if 2 <= n <= 4: return "Repeat (2–4 order months)"
            return "Loyal (5+ order months)"

        cust_orders = tx.groupby("customer_id").agg(orders=("order_month", "nunique"),revenue=("revenue", "sum")).reset_index()
        cust_orders["segment"] = cust_orders["orders"].apply(seg)

        seg_table = (
            cust_orders.groupby("segment", as_index=False)
                    .agg(Customers=("customer_id", "nunique"),
                            Revenue=("revenue", "sum"),
                            Avg_Orders=("orders", "mean"))
        )

        seg_table = seg_table.sort_values("Revenue", ascending=False)
        total_rev_all = seg_table["Revenue"].sum()
        if total_rev_all:
            seg_table["Revenue Share"] = seg_table["Revenue"] / total_rev_all

        #Customer segmentation logic ends here

        
        #Metrics for customers
        k1, k2, k3 = st.columns(3)
        k1.metric("Repeat Purchase Rate", f"{repeat_rate:.0f}%")
        k2.metric("Customers (≥2 order months)", f"{repeat_customers:,}")
        k3.metric("Total Customers", f"{total_customers:,}")


        #Individual customer revenue
        
        customer_revenue_df = run_query(load_sql("queries/customer_revenue.txt"))
        c1, c2 = st.columns([1, 1])
        with c1:
            top_n = st.slider("Top customers", min_value=3, max_value=20, value=5, step=1)
        with c2:
            sel_categories = sorted(customer_revenue_df["category"].dropna().unique().tolist())
            sort_order = st.multiselect("Filter categories", categories)

        if customer_revenue_df.empty:
            st.info("No customer/category revenue data available.")
        else:
            df = customer_revenue_df.copy()
            if sort_order:
                df = df[df["category"].isin(sort_order)]

            if df.empty:
                st.info("No rows match the selected categories.")
            else:
                agg = (
                    df.groupby("customer_name")
                    .agg(
                        total_revenue=("total_revenue", "sum"),
                        categories=("category", lambda x: ", ".join(sorted(set(x))))
                    )
                    .reset_index()
                )
            top_customers = agg.sort_values("total_revenue", ascending=False).head(top_n)

            tcol, ccol = st.columns([1, 1], gap="large")

            with tcol:
                st.subheader("Top Customers (Aggregated Across Selected Categories)")
                view = top_customers.rename(columns={
                    "customer_name": "Customer",
                    "total_revenue": "Revenue",
                    "categories": "Categories"
                })
                st.dataframe(
                    view.assign(Revenue=lambda d: d["Revenue"].round(2)),
                    use_container_width=True,
                    hide_index=True
                )
                # Optional download
                st.download_button(
                    "⬇️ Download table (CSV)",
                    data=view.to_csv(index=False).encode("utf-8"),
                    file_name="top_customers_aggregated.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

            with ccol:

                # For a clean horizontal bar: sort ascending so largest appears at top after plotting
                plot_df = top_customers.sort_values("total_revenue", ascending=True).copy()
                plot_df["hover_cat"] = plot_df["categories"]
                fig = px.bar(
                    plot_df,
                    x="total_revenue",
                    y="customer_name",
                    orientation="h",
                    title=(
                        f"Top {len(plot_df)} Customers by Revenue"
                        + (f" — {', '.join(sort_order)}" if sort_order else " — All Categories")
                    ),
                    labels={"total_revenue": "Revenue", "customer_name": "Customer"},
                    text=plot_df["total_revenue"].map(lambda v: f"${v:,.0f}")
                )
                fig.update_traces(
                    textposition="outside",
                    cliponaxis=False,
                    hovertemplate="Customer: %{y}<br>Categories: %{customdata}<br>Revenue: $%{x:,.0f}<extra></extra>",
                    customdata=plot_df["hover_cat"]
                )
                fig.update_layout(
                    template="plotly_white",
                    margin=dict(l=10, r=10, t=80, b=10),
                )
                fig.update_xaxes(tickprefix="$", separatethousands=True)
                st.plotly_chart(fig, use_container_width=True)



        


        def make_checkpoint_bars(cohort_retention: pd.DataFrame, checkpoints=(1,2,3), title="Checkpoint Retention by Cohort"):
            bars = (cohort_retention.copy() * 100)
            bars = bars[[c for c in bars.columns if c in checkpoints]]
            bars_long = (
                bars.reset_index()
                    .melt(id_vars="cohort_month", var_name="Months since first purchase", value_name="Retention %")
                    .dropna()
            )
            fig = px.bar(
                bars_long,
                x="cohort_month",
                y="Retention %",
                color="Months since first purchase",
                barmode="group",
                title=title,
                labels={"cohort_month": "Cohort (first purchase month)"},
                text=bars_long["Retention %"].round(0).astype(int).astype(str) + "%"
            )
            fig.update_traces(textposition="outside", cliponaxis=False)
            fig.update_xaxes(
                tickmode="array",
                tickvals=bars_long["cohort_month"].unique(), 
                tickangle=-45                            
            )
            fig.update_layout(template="plotly_white", margin=dict(l=10, r=10, t=80, b=10))
            return fig
        
        st.subheader("Checkpoint Retention By Cohort")
        fig_chk = make_checkpoint_bars(cohort_retention, checkpoints=(1,2,3,4))
        st.plotly_chart(fig_chk, use_container_width=True)

        


        #Customer segmentation table
        st.subheader("Top Customer Segments by Revenue")
        st.dataframe(
            seg_table.assign(
                Revenue=lambda d: d["Revenue"].round(2),
                Avg_Orders=lambda d: d["Avg_Orders"].round(2),
                **({"Revenue Share": (seg_table["Revenue Share"]*100).round(0).astype("Int64").astype(str) + "%"}
                if "Revenue Share" in seg_table else {})
            ),
            use_container_width=True,
            hide_index=True
        )

        #CSV download for further analysis
        st.download_button(
        "⬇️ Download segments (CSV)",
        data=seg_table.to_csv(index=False).encode("utf-8"),
        file_name="customer_segments.csv",
        mime="text/csv",
        use_container_width=True,
        )

        month2_avg = (cohort_retention[2].mean() * 100) if 2 in cohort_retention.columns else None
        insight = ""
        if month2_avg is not None:
            insight = f"Retention averages ~{month2_avg:.0f}% by the 2nd month; targeted promotions could improve repeat orders."
        else:
            insight = "Retention drops after the early months; targeted promotions could improve repeat orders."
        st.info(insight)

