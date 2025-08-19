import os
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import sqlite3

conn = sqlite3.connect("retail_sales.db")

st.set_page_config(page_title="Data Analysis Dashboard", layout="wide")
st.title("Data Analysis Dashboard")
st.subheader('Monthly Key Performance Indicators')
tab1,tab2,tab3,tab4 = st.tabs(["Revenue","Total Orders", "Units sold", "Average Order Value"])
kpi_df = pd.read_sql_query(open("queries/main_kpi_summary.txt").read(), conn)
masking_dict = {"total_revenue": "Revenue", "total_orders":"Orders", "units_sold": "Units Sold", "average_order_value":"Average Order Value"}

#Key Performance Indicator Graphing
def make_kpi_line(df: pd.DataFrame, value_col: str, use_moving_average: bool) -> "plotly.graph_objs._figure.Figure":
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
        fig.add_scatter(
            x=d["month_year"],
            y=d[ma_col],
            mode="lines",
            name="3-mo avg",
        )

    # Peak & Low annotations
    peak = d.loc[d[value_col].idxmax()]
    low = d.loc[d[value_col].idxmin()]

    is_currency = value_col in {"total_revenue", "average_order_value"}
    y_prefix = "$" if is_currency else ""
    hover_val_fmt = "$%{y:,.0f}" if is_currency else "%{y:,.0f}"

    fig.add_annotation(
        x=peak["month_year"],
        y=peak[value_col],
        text=f"Peak: {y_prefix}{peak[value_col]:,.0f}",
        showarrow=True,
        arrowhead=2,
        yshift=10,
    )
    fig.add_annotation(
        x=low["month_year"],
        y=low[value_col],
        text=f"Low: {y_prefix}{low[value_col]:,.0f}",
        showarrow=True,
        arrowhead=2,
        yshift=-10,
    )

    fig.update_traces(hovertemplate=f"%{{x|%b %Y}}<br>{display_name}: {hover_val_fmt}")
    fig.update_layout(
        template="plotly_white",
        hovermode="x unified",
        margin=dict(l=10, r=10, t=50, b=10),
        yaxis_tickprefix=y_prefix,
        yaxis_separatethousands=True,
        legend_title_text="",
    )
    fig.update_xaxes(
        rangeslider_visible=True,
        rangeselector=dict(
            buttons=[
                dict(count=3, step="month", stepmode="backward", label="3M"),
                dict(count=6, step="month", stepmode="backward", label="6M"),
                dict(count=9, step="month", stepmode="backward", label="9M"),
                dict(step="all", label="All"),
            ]
        ),
    )

    fig.update_layout(
    margin=dict(l=10, r=10, t=100, b=70)
)
    return fig

with tab1:
    rev_fig = make_kpi_line(kpi_df, "total_revenue", use_moving_average=True)
    st.plotly_chart(rev_fig, use_container_width=True)

with tab2:
    orders_fig = make_kpi_line(kpi_df, "total_orders", use_moving_average=False)
    st.plotly_chart(orders_fig, use_container_width=True)
with tab3:
    units_sold_fig = make_kpi_line(kpi_df, "units_sold", use_moving_average=False)
    st.plotly_chart(units_sold_fig, use_container_width=True)
with tab4:
    aov_fig = make_kpi_line(kpi_df, "average_order_value", use_moving_average=False)
    st.plotly_chart(aov_fig, use_container_width=True)

#Logic for KPI ends here. Add insight boxes too


#Start working on Mix Tab(Category and region insights)
st.subheader("Category and Region Insights")
cat_reg_df = pd.read_sql_query(open("queries/top_category.txt").read(), conn)
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

mix_tab, = st.tabs(["Mix"])


with mix_tab:
    # Pareto
    pareto_fig, info = make_pareto_chart(cat_reg_df, "category", "total_revenue", cutoff=0.80,
                                         title="Pareto: Revenue by Category")
    st.plotly_chart(pareto_fig, use_container_width=True)

    # Insight box
    pct_str = f"{info['pct']*100:.0f}%"
    lead_list = ", ".join(info["top_labels"])
    st.info(
        f"Top **{info['top_k']}** categories make up **{pct_str}** of revenue. "
        f"Leaders: **{lead_list}**."
    )

#Add region x category heatmap to show how each region's categories are distributed
rc_df = pd.read_sql_query(open("queries/region_category_heatmap.txt").read(), conn)

# Total revenue by region
region_totals = rc_df.groupby("region", as_index=False)["total_revenue"].sum()
top_region_row = region_totals.loc[region_totals["total_revenue"].idxmax()]
top_region = top_region_row["region"]
top_region_revenue = top_region_row["total_revenue"]

# Top category within the top region
top_cat_row = (
    rc_df[rc_df["region"] == top_region]
    .groupby("category", as_index=False)["total_revenue"].sum()
    .sort_values("total_revenue", ascending=False)
    .iloc[0]
)
top_category_in_region = top_cat_row["category"]
top_category_revenue = top_cat_row["total_revenue"]

fig_tree = px.treemap(
    rc_df,
    path=["region", "category"],   # hierarchy
    values="total_revenue",
    title="Revenue by Region and Category",
)
fig_tree.update_traces(
    hovertemplate=(
        "Path: %{label}<br>"
        "Revenue: $%{value:,.0f}<extra></extra>"
    )
)
fig_tree.update_layout(
    template="plotly_white",
    margin=dict(l=10, r=10, t=80, b=10),
    title=dict(x=0.5, xanchor="center", yanchor="top", pad=dict(t=20))
)
st.plotly_chart(fig_tree, use_container_width=True)

# Sort regions by total revenue (descending)
region_order = (
    region_totals.sort_values("total_revenue", ascending=False)["region"].tolist()
)

fig_stack = px.bar(
    rc_df,
    x="region",
    y="total_revenue",
    color="category",
    title="Which Regions Make the Most (and What’s Driving It)",
)
fig_stack.update_traces(
    hovertemplate="%{x}<br>%{fullData.name}: $%{y:,.0f}<extra></extra>"
)
fig_stack.update_layout(
    barmode="stack",
    template="plotly_white",
    margin=dict(l=10, r=10, t=80, b=10),
    title=dict(x=0.5, xanchor="center", yanchor="top", pad=dict(t=20)),
    legend_title_text="Category",
)
fig_stack.update_xaxes(categoryorder="array", categoryarray=region_order)
fig_stack.update_yaxes(tickprefix="$", separatethousands=True, title_text="Revenue")
st.plotly_chart(fig_stack, use_container_width=True)

rev_str = f"${top_region_revenue:,.0f}"
#Correct the dollar sign here. Make sure you fix this bug
cat_rev_str =  f"{top_category_revenue:,.0f}"

st.info(
    f"**{top_region}** is the top region with **{rev_str}** in revenue. Within **{top_region}**, **{top_category_in_region}** leads at **{cat_rev_str}**."
)

#Store performance
st.subheader("Store Performance")
col1, col2 = st.columns([1,2])
all_store_df = pd.read_sql_query(open("queries/all_stores_performance.txt").read(), conn)
with col1:
    st.dataframe(all_store_df)
with col2:
    st.write("Select which store you want to look at.")
    selected_store = st.selectbox("Choose a store", options=all_store_df['store_name'].to_list())

    kpi_tab, products_tab = st.tabs(["KPI Trends", "Top Products"])

    with kpi_tab:
        kpi_store_df = pd.read_sql_query(open("queries/store_kpi_summary.txt").read(), conn,params=(selected_store,))
        # KPI cards (last month values)
        if not kpi_store_df.empty:
            last = kpi_store_df.iloc[-1]
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Revenue (last)", f"${last['total_revenue']:,.0f}")
            c2.metric("Orders (last)", f"{int(last['total_orders']):,}")
            c3.metric("Units (last)", f"{int(last['units_sold']):,}")
            c4.metric("AOV (last)", f"${last['average_order_value']:,.0f}")

            # One selector to switch the trend metric (reuses your make_kpi_line)
            metric_map = {
                "Revenue": "total_revenue",
                "Orders": "total_orders",
                "Units Sold": "units_sold",
                "Average Order Value": "average_order_value",
            }
            chosen_metric_label = st.selectbox("Trend metric", list(metric_map.keys()))
            chosen_col = metric_map[chosen_metric_label]

            fig = make_kpi_line(kpi_store_df, chosen_col, use_moving_average=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data for this store yet.")
    
    with products_tab:
        option_select = st.selectbox("Select a chart to view",options = ["Top Categories","Top Products"])
        print("2cw")
        if option_select == "Top Categories":
            cat_df = pd.read_sql_query(open("queries/all_stores_category.txt").read(), conn, params=(selected_store,))
            if not cat_df.empty:
                # Sort for horizontal bar & compute share
                cat_df = cat_df.sort_values("revenue", ascending=True)
                total_rev = cat_df["revenue"].sum()
                cat_df["share"] = (cat_df["revenue"] / total_rev).fillna(0)

                fig_cat = px.bar(
                    cat_df,
                    x="revenue",
                    y="category",
                    orientation="h",
                    title=f"Top Categories by Revenue — {selected_store}",
                    labels={"revenue": "Revenue", "category": "Category"},
                    text=cat_df["share"].map(lambda x: f"{x*100:.0f}%"),
                )
                fig_cat.update_traces(
                    hovertemplate="%{y}<br>Revenue: $%{x:,.0f}<br>Share: %{text}<extra></extra>",
                    textposition="outside",
                    cliponaxis=False,
                )
                fig_cat.update_layout(
                    template="plotly_white",
                    margin=dict(l=10, r=10, t=80, b=10),
                    hovermode="y unified",
                    xaxis_title="Revenue",
                    yaxis_title="Category",
                )
                fig_cat.update_xaxes(tickprefix="$", separatethousands=True)
                st.plotly_chart(fig_cat, use_container_width=True)

                # Insight: top category + share
                top_row = cat_df.sort_values("revenue", ascending=False).iloc[0]
                st.caption(
                    f"“{top_row['category']}” leads this store with "
                    f"${top_row['revenue']:,.0f} ({top_row['share']*100:.0f}% of category revenue)."
                )
            else:
                st.info("No category revenue found for this store.")
            
        if option_select == "Top Products":
            prod_df = pd.read_sql_query(open("queries/all_stores_products.txt").read(),conn,params=(selected_store,))
            if not prod_df.empty:
                prod_df = prod_df.sort_values("revenue", ascending=True)  # for horiz bar
                fig_top = px.bar(
                    prod_df,
                    x="revenue",
                    y="product_name",
                    orientation="h",
                    title=f"Top Products by Revenue — {selected_store}",
                    labels={"revenue": "Revenue", "product_name": "Product"},
                )
                fig_top.update_layout(
                    template="plotly_white",
                    margin=dict(l=10, r=10, t=80, b=10),
                    hovermode="y unified",
                )
                fig_top.update_xaxes(tickprefix="$", separatethousands=True)
                st.plotly_chart(fig_top, use_container_width=True)

                # Optional quick insight
                total_rev = prod_df["revenue"].sum()
                top3 = prod_df.sort_values("revenue", ascending=False).head(3)
                share = top3["revenue"].sum() / total_rev if total_rev else 0
                st.caption(
                    f"Top 3 products contribute {share*100:.0f}% of store revenue."
                )
            else:
                st.info("No product sales found for this store.")
    
