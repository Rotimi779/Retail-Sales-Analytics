"""
Revenue Forecasting Tab for Retail Sales Analytics Dashboard
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import sqlite3
from datetime import datetime, timedelta

def get_monthly_revenue_data(db_path='retail_sales.db'):
    """
    Fetch monthly revenue data from the database
    """
    conn = sqlite3.connect(db_path)
    
    query = """
    SELECT 
        strftime('%Y-%m', s.sale_date) as month,
        SUM(s.quantity * p.price) as revenue
    FROM sales s
    JOIN products p ON s.product_id = p.product_id
    GROUP BY strftime('%Y-%m', s.sale_date)
    ORDER BY month
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # Convert month to datetime
    df['month'] = pd.to_datetime(df['month'])
    df = df.set_index('month')
    
    return df

def forecast_revenue(revenue_series, periods=3):
    """
    Forecast future revenue using Holt-Winters Exponential Smoothing
    Adapts to available data:
    - 24+ months: Full seasonal model (trend + seasonality)
    - 12-23 months: Trend-only model (no seasonality)
    - <12 months: Simple exponential smoothing
    
    Parameters:
    - revenue_series: pandas Series with datetime index and revenue values
    - periods: number of months to forecast (default 3)
    
    Returns:
    - forecast: predicted values
    - fitted_values: historical fitted values
    - confidence_intervals: upper and lower bounds
    """
    try:
        n_obs = len(revenue_series)
        
        # Choose model based on available data
        if n_obs >= 24:
            # Full seasonal model (2+ years of data)
            model = ExponentialSmoothing(
                revenue_series,
                seasonal_periods=12,
                trend='add',
                seasonal='add',
                initialization_method='estimated'
            )
            model_type = "Seasonal (Trend + Seasonality)"
        
        elif n_obs >= 12:
            # Trend-only model (1-2 years of data)
            model = ExponentialSmoothing(
                revenue_series,
                trend='add',
                seasonal=None,
                initialization_method='estimated'
            )
            model_type = "Trend-Only"
        
        else:
            # Simple exponential smoothing (<1 year of data)
            model = ExponentialSmoothing(
                revenue_series,
                trend=None,
                seasonal=None,
                initialization_method='estimated'
            )
            model_type = "Simple"
        
        # Fit the model
        fitted_model = model.fit()
        
        # Get forecast
        forecast = fitted_model.forecast(steps=periods)
        fitted_values = fitted_model.fittedvalues
        
        # Calculate prediction intervals (approximate)
        residuals = revenue_series - fitted_values
        std_residual = residuals.std()
        
        # 95% confidence interval (approximately ±2 std deviations)
        lower_bound = forecast - 2 * std_residual
        upper_bound = forecast + 2 * std_residual
        
        # Show warning if not using full seasonal model
        if n_obs < 24:
            st.warning(
                f"⚠️ Using **{model_type}** model due to limited data ({n_obs} months). "
                f"Full seasonal forecasting requires 24+ months of historical data for best results."
            )
        
        return forecast, fitted_values, (lower_bound, upper_bound)
    
    except Exception as e:
        st.error(f"Error in forecasting: {str(e)}")
        return None, None, (None, None)

def create_forecast_chart(historical_data, forecast, fitted_values, confidence_intervals, forecast_periods):
    """
    Create an interactive Plotly chart showing historical data and forecast
    """
    fig = go.Figure()
    
    # Historical actual data
    fig.add_trace(go.Scatter(
        x=historical_data.index,
        y=historical_data['revenue'],
        mode='lines+markers',
        name='Actual Revenue',
        line=dict(color='#1f77b4', width=2),
        marker=dict(size=6)
    ))
    
    # Fitted values (model fit to historical data)
    fig.add_trace(go.Scatter(
        x=fitted_values.index,
        y=fitted_values,
        mode='lines',
        name='Model Fit',
        line=dict(color='#ff7f0e', width=2, dash='dot'),
        opacity=0.7
    ))
    
    # Forecast
    fig.add_trace(go.Scatter(
        x=forecast.index,
        y=forecast,
        mode='lines+markers',
        name='Forecast',
        line=dict(color='#2ca02c', width=3, dash='dash'),
        marker=dict(size=8, symbol='diamond')
    ))
    
    # Confidence interval
    lower_bound, upper_bound = confidence_intervals
    if lower_bound is not None and upper_bound is not None:
        fig.add_trace(go.Scatter(
            x=forecast.index.tolist() + forecast.index.tolist()[::-1],
            y=upper_bound.tolist() + lower_bound.tolist()[::-1],
            fill='toself',
            fillcolor='rgba(44, 160, 44, 0.2)',
            line=dict(color='rgba(255,255,255,0)'),
            name='95% Confidence Interval',
            showlegend=True
        ))
    
    fig.update_layout(
        title=f'Revenue Forecast - Next {forecast_periods} Months',
        xaxis_title='Month',
        yaxis_title='Revenue ($)',
        hovermode='x unified',
        height=500,
        template='plotly_white'
    )
    
    return fig

def render_forecasting_tab():
    """
    Main function to render the forecasting tab
    Call this function inside your st.tabs() section
    """
    st.subheader("📈 Revenue Forecasting")
    
    st.markdown("""
    This forecast uses **Holt-Winters Exponential Smoothing**, which captures:
    - **Trend**: Overall growth or decline in revenue
    - **Seasonality**: Recurring monthly patterns
    - **Level**: Base revenue amount
    """)
    
    # Fetch data
    try:
        df_revenue = get_monthly_revenue_data()
        
        n_months = len(df_revenue)
        
        # Show data availability status
        if n_months < 12:
            st.info(
                f"📊 **{n_months} months of data available.** "
                f"Using simple exponential smoothing. For trend detection, collect 12+ months. "
                f"For seasonal patterns, collect 24+ months."
            )
        elif n_months < 24:
            st.info(
                f"📊 **{n_months} months of data available.** "
                f"Using trend-based forecasting. For full seasonal analysis, collect 24+ months."
            )
        
        # Forecast settings
        col1, col2 = st.columns([3, 1])
        with col2:
            forecast_periods = st.selectbox(
                "Months to Forecast",
                options=[1, 2, 3, 4, 5, 6],
                index=2  # default to 3 months
            )
        
        # Generate forecast
        forecast, fitted_values, confidence_intervals = forecast_revenue(
            df_revenue['revenue'], 
            periods=forecast_periods
        )
        
        if forecast is not None:
            # Create chart
            fig = create_forecast_chart(df_revenue, forecast, fitted_values, confidence_intervals, forecast_periods)
            st.plotly_chart(fig, use_container_width=True)
            
            # Forecast table
            st.subheader("📊 Forecast Summary")
            
            forecast_df = pd.DataFrame({
                'Month': forecast.index.strftime('%B %Y'),
                'Forecasted Revenue': forecast.values,
                'Lower Bound (95%)': confidence_intervals[0].values,
                'Upper Bound (95%)': confidence_intervals[1].values
            })
            
            # Format as currency
            for col in ['Forecasted Revenue', 'Lower Bound (95%)', 'Upper Bound (95%)']:
                forecast_df[col] = forecast_df[col].apply(lambda x: f'${x:,.2f}')
            
            st.dataframe(forecast_df, use_container_width=True, hide_index=True)
            
            # Key insights
            st.subheader("💡 Key Insights")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                avg_forecast = forecast.mean()
                st.metric(
                    "Avg Forecasted Revenue",
                    f"${avg_forecast:,.0f}"
                )
            
            with col2:
                last_actual = df_revenue['revenue'].iloc[-1]
                first_forecast = forecast.iloc[0]
                change = ((first_forecast - last_actual) / last_actual) * 100
                st.metric(
                    "Month-over-Month Change",
                    f"{change:+.1f}%",
                    delta_color="normal"
                )
            
            with col3:
                total_forecast = forecast.sum()
                st.metric(
                    f"Total Next {forecast_periods} Months",
                    f"${total_forecast:,.0f}"
                )
            
            # Methodology explanation
            with st.expander("📚 How Does This Forecasting Work?"):
                st.markdown("""
                ### Holt-Winters Exponential Smoothing
                
                This forecasting method is ideal for retail sales because it accounts for:
                
                1. **Level**: The baseline revenue amount
                2. **Trend**: Whether revenue is generally increasing or decreasing over time
                3. **Seasonality**: Recurring patterns (e.g., holiday spikes, slow summer months)
                
                #### Why Use This Method?
                - ✅ **Industry Standard**: Used by companies like Amazon, Walmart for sales forecasting
                - ✅ **Fast & Reliable**: Trains in seconds, good accuracy with limited data
                - ✅ **Interpretable**: Easy to explain to stakeholders
                - ✅ **Handles Seasonality**: Captures monthly/yearly patterns automatically
                
                #### Model Parameters
                - **Seasonal Period**: 12 months (captures yearly cycles)
                - **Trend**: Additive (revenue changes by a constant amount)
                - **Seasonality**: Additive (seasonal effect is constant)
                - **Confidence Interval**: 95% (shown as shaded area)
                
                #### Limitations
                - Assumes past patterns will continue
                - Cannot predict sudden market disruptions
                - Works best with 24+ months of historical data
                - Does not account for external factors (marketing campaigns, competitors, etc.)
                """)
        
        else:
            st.error("Unable to generate forecast. Please check your data.")
    
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        st.info("Make sure your database path is correct and contains the necessary tables.")
