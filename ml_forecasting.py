"""
Feature-Based Revenue Forecasting for Retail Sales Analytics Dashboard

This module frames revenue forecasting as a supervised ML problem:
instead of relying purely on the time-series sequence (Holt-Winters),
it engineers features (calendar, lag, rolling-window, business metrics)
and trains regression models to predict monthly revenue.

It compares multiple models using walk-forward (time-series) validation
and surfaces feature importance.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import sqlite3

from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from xgboost import XGBRegressor


# ─────────────────────────────────────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────────────────────────────────────
def get_monthly_features(db_path: str = "retail_sales.db") -> pd.DataFrame:
    """
    Build a monthly aggregate table from the database with all the raw
    columns we need to engineer features from.
    """
    conn = sqlite3.connect(db_path)

    query = """
    SELECT
        strftime('%Y-%m', s.sale_date)  AS month,
        SUM(s.quantity * p.price)       AS revenue,
        COUNT(DISTINCT s.sale_id)       AS orders,
        SUM(s.quantity)                 AS units,
        COUNT(DISTINCT s.customer_id)   AS unique_customers,
        COUNT(DISTINCT s.product_id)    AS unique_products
    FROM sales s
    JOIN products p ON s.product_id = p.product_id
    GROUP BY strftime('%Y-%m', s.sale_date)
    ORDER BY month
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    df["month"] = pd.to_datetime(df["month"])
    df = df.sort_values("month").reset_index(drop=True)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# FEATURE ENGINEERING
# ─────────────────────────────────────────────────────────────────────────────
def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create calendar, lag, and rolling-window features from the monthly data.

    NOTE on leakage: lag and rolling features are all computed with .shift(),
    so every feature for month M only uses data from months strictly before M.
    """
    d = df.copy()

    # ── Calendar features ────────────────────────────────────────────────
    d["month_num"] = d["month"].dt.month
    d["quarter"]   = d["month"].dt.quarter
    d["year"]      = d["month"].dt.year
    d["is_q4"]     = (d["quarter"] == 4).astype(int)
    d["is_jan"]    = (d["month_num"] == 1).astype(int)

    # Cyclical encoding of month (so Dec and Jan are "close")
    d["month_sin"] = np.sin(2 * np.pi * d["month_num"] / 12)
    d["month_cos"] = np.cos(2 * np.pi * d["month_num"] / 12)

    # ── Lag features (previous revenue) ──────────────────────────────────
    d["revenue_lag1"]  = d["revenue"].shift(1)   # last month
    d["revenue_lag3"]  = d["revenue"].shift(3)   # 3 months ago
    d["revenue_lag12"] = d["revenue"].shift(12)  # same month last year

    # ── Rolling-window features (shifted to avoid leakage) ───────────────
    d["revenue_ma3"]  = d["revenue"].shift(1).rolling(3).mean()
    d["revenue_ma6"]  = d["revenue"].shift(1).rolling(6).mean()
    d["revenue_std3"] = d["revenue"].shift(1).rolling(3).std()

    # ── Business features (also lagged — we won't know this month's
    #     orders/customers when forecasting ahead) ──────────────────────
    d["orders_lag1"]            = d["orders"].shift(1)
    d["units_lag1"]             = d["units"].shift(1)
    d["unique_customers_lag1"]  = d["unique_customers"].shift(1)

    return d


FEATURE_COLS = [
    "month_num", "quarter", "is_q4", "is_jan",
    "month_sin", "month_cos",
    "revenue_lag1", "revenue_lag3", "revenue_lag12",
    "revenue_ma3", "revenue_ma6", "revenue_std3",
    "orders_lag1", "units_lag1", "unique_customers_lag1",
]


# ─────────────────────────────────────────────────────────────────────────────
# WALK-FORWARD VALIDATION
# ─────────────────────────────────────────────────────────────────────────────
def walk_forward_validate(model, X: pd.DataFrame, y: pd.Series, min_train: int = 24):
    """
    Time-series cross-validation. For each step:
      - train on all months up to t
      - predict month t+1
    This prevents look-ahead bias (never uses future data to predict past).

    Returns: (actuals, predictions) aligned arrays for the test portion.
    """
    actuals, predictions = [], []

    for t in range(min_train, len(X)):
        X_train, y_train = X.iloc[:t], y.iloc[:t]
        X_test,  y_test  = X.iloc[t:t + 1], y.iloc[t:t + 1]

        model.fit(X_train, y_train)
        pred = model.predict(X_test)[0]

        actuals.append(y_test.values[0])
        predictions.append(pred)

    return np.array(actuals), np.array(predictions)


def evaluate(actuals: np.ndarray, predictions: np.ndarray) -> dict:
    """Compute standard regression metrics."""
    mae  = mean_absolute_error(actuals, predictions)
    rmse = np.sqrt(mean_squared_error(actuals, predictions))
    # MAPE — guard against division by zero
    mask = actuals != 0
    mape = np.mean(np.abs((actuals[mask] - predictions[mask]) / actuals[mask])) * 100
    return {"MAE": mae, "RMSE": rmse, "MAPE": mape}


# ─────────────────────────────────────────────────────────────────────────────
# STREAMLIT TAB
# ─────────────────────────────────────────────────────────────────────────────
def render_ml_forecasting_tab():
    """Render the feature-based ML forecasting section."""

    st.subheader("🤖 Feature-Based Revenue Forecasting (ML)")

    st.markdown("""
    This approach frames forecasting as a **supervised machine learning problem**.
    Instead of relying only on the revenue sequence, it engineers **features**
    (calendar, lag, rolling-window, and business metrics) and trains regression
    models to predict monthly revenue.
    """)

    with st.expander("🔍 How is this different from Holt-Winters?"):
        st.markdown("""
        | Aspect | Holt-Winters | Feature-Based ML |
        |---|---|---|
        | **Approach** | Statistical time series | Supervised regression |
        | **Inputs** | Just the revenue sequence | Engineered features |
        | **Models** | One model | Compare LR / RF / XGBoost |
        | **Interpretability** | Trend + seasonal components | Feature importance |
        | **Flexibility** | Fixed structure | Add any feature you want |

        **Feature-based forecasting** lets you answer *"what drives revenue?"*,
        not just *"what will revenue be?"*
        """)

    try:
        # ── Load & engineer ──────────────────────────────────────────────
        raw = get_monthly_features()
        n_months = len(raw)

        if n_months < 30:
            st.warning(
                f"⚠️ Only {n_months} months of data available. Feature-based "
                f"forecasting with walk-forward validation needs ~30+ months "
                f"to be meaningful (it reserves the first 24 for the initial "
                f"training window). Results may be unstable."
            )

        featured = engineer_features(raw)

        # Drop rows with NaN features (the first 12 months — no lag12 yet)
        model_data = featured.dropna(subset=FEATURE_COLS + ["revenue"]).reset_index(drop=True)

        if len(model_data) < 12:
            st.error(
                f"Not enough usable data after feature engineering "
                f"({len(model_data)} rows). Need more historical months."
            )
            return

        X = model_data[FEATURE_COLS]
        y = model_data["revenue"]

        # min_train scales with how much data we have
        min_train = min(24, max(6, len(model_data) // 2))

        # ── Define models ────────────────────────────────────────────────
        models = {
            "Linear Regression": LinearRegression(),
            "Random Forest":     RandomForestRegressor(n_estimators=100, random_state=42),
            "XGBoost":           XGBRegressor(n_estimators=100, random_state=42, verbosity=0),
        }

        # ── Walk-forward validation for each model ───────────────────────
        st.markdown("### 📊 Model Comparison")
        st.caption(
            f"Evaluated with **walk-forward validation** — train on all months "
            f"up to *t*, predict month *t+1*, repeat. Initial training window: "
            f"{min_train} months."
        )

        results = {}
        predictions_by_model = {}
        with st.spinner("Training and validating models..."):
            for name, model in models.items():
                actuals, preds = walk_forward_validate(model, X, y, min_train=min_train)
                results[name] = evaluate(actuals, preds)
                predictions_by_model[name] = (actuals, preds)

        # ── Results table ────────────────────────────────────────────────
        results_df = pd.DataFrame(results).T
        results_df = results_df.round(2)

        # Identify best model (lowest MAE)
        best_model_name = results_df["MAE"].idxmin()

        display_df = results_df.copy()
        display_df["MAE"]  = display_df["MAE"].apply(lambda x: f"${x:,.0f}")
        display_df["RMSE"] = display_df["RMSE"].apply(lambda x: f"${x:,.0f}")
        display_df["MAPE"] = display_df["MAPE"].apply(lambda x: f"{x:.1f}%")

        st.dataframe(display_df, use_container_width=True)
        st.success(
            f"🏆 **Best model: {best_model_name}** "
            f"(lowest MAE — average prediction error of "
            f"${results_df.loc[best_model_name, 'MAE']:,.0f})"
        )

        with st.expander("📚 What do these metrics mean?"):
            st.markdown("""
            - **MAE (Mean Absolute Error)** — average dollar amount the forecast
              is off by. Lower is better. Easy to explain to stakeholders.
            - **RMSE (Root Mean Squared Error)** — like MAE but penalizes large
              misses more heavily. Sensitive to outliers.
            - **MAPE (Mean Absolute Percentage Error)** — average error as a
              percentage. Useful for comparing across different revenue scales.
              Under 10% is generally considered a good forecast.
            """)

        # ── Actual vs Predicted chart for best model ─────────────────────
        st.markdown(f"### 📈 Actual vs. Predicted — {best_model_name}")

        actuals, preds = predictions_by_model[best_model_name]
        test_months = model_data["month"].iloc[min_train:].reset_index(drop=True)

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=test_months, y=actuals,
            mode="lines+markers", name="Actual Revenue",
            line=dict(color="#1f77b4", width=2),
        ))
        fig.add_trace(go.Scatter(
            x=test_months, y=preds,
            mode="lines+markers", name="Predicted Revenue",
            line=dict(color="#2ca02c", width=2, dash="dash"),
        ))
        fig.update_layout(
            title=f"{best_model_name}: Walk-Forward Predictions",
            xaxis_title="Month", yaxis_title="Revenue ($)",
            hovermode="x unified", height=450, template="plotly_white",
        )
        fig.update_yaxes(tickprefix="$", separatethousands=True)
        st.plotly_chart(fig, use_container_width=True)

        # ── Feature importance (tree-based models only) ──────────────────
        st.markdown("### 🎯 What Drives Revenue?")
        st.caption(
            "Feature importance from the best tree-based model — which inputs "
            "the model relies on most to predict revenue."
        )

        # Use the best model if it's tree-based, else fall back to Random Forest
        if best_model_name in ("Random Forest", "XGBoost"):
            fi_model_name = best_model_name
        else:
            fi_model_name = "Random Forest"

        fi_model = models[fi_model_name]
        fi_model.fit(X, y)  # fit on all data for importance

        importance_df = pd.DataFrame({
            "feature": FEATURE_COLS,
            "importance": fi_model.feature_importances_,
        }).sort_values("importance", ascending=True)

        fig_imp = px.bar(
            importance_df, x="importance", y="feature", orientation="h",
            title=f"Feature Importance ({fi_model_name})",
            labels={"importance": "Importance", "feature": "Feature"},
        )
        fig_imp.update_layout(template="plotly_white", height=500,
                              margin=dict(l=10, r=10, t=60, b=10))
        st.plotly_chart(fig_imp, use_container_width=True)

        top_feature = importance_df.iloc[-1]["feature"]
        st.info(
            f"💡 **{top_feature}** is the strongest predictor of monthly revenue. "
            f"This tells the business which signals matter most when planning ahead."
        )

        # ── Next-month prediction from best model ────────────────────────
        st.markdown("### 🔮 Next Month Prediction")

        best_model = models[best_model_name]
        best_model.fit(X, y)

        # The most recent fully-featured row predicts the "next" step
        latest_features = X.iloc[[-1]]
        next_pred = best_model.predict(latest_features)[0]
        last_actual = y.iloc[-1]
        change = ((next_pred - last_actual) / last_actual) * 100

        c1, c2 = st.columns(2)
        c1.metric("Predicted Next-Month Revenue", f"${next_pred:,.0f}")
        c2.metric("vs. Last Actual Month", f"{change:+.1f}%")

        st.caption(
            "⚠️ Note: this is a one-step-ahead estimate using the most recent "
            "feature values. For multi-month forecasts, features would need to "
            "be projected forward iteratively."
        )

    except Exception as e:
        st.error(f"Error in ML forecasting: {str(e)}")
        st.info("Make sure your database exists and contains sales + products tables.")
