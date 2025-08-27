# Retail Sales Analytics Dashboard  

An interactive **Streamlit + Plotly** dashboard for exploring retail sales data, inventory risks, store performance, and customer retention.  
The project uses **SQLite** as a lightweight analytical database, rebuilt automatically from CSV inputs.

---

## 🚀 Features  

### 1. **Monthly Key Performance Indicators (KPIs)**  
- **Revenue** = Σ (*quantity × unit_price*)  
- **Total Orders** = Count of customer orders per month  
- **Units Sold** = Σ (*quantity*)  
- **Average Order Value (AOV)** = Revenue ÷ Orders  
- Includes **3-month moving averages** for trend smoothing.  

### 2. **Category & Region Insights**  
- **Pareto Chart** → Identify the top categories driving ~80% of revenue.  
- **Treemap** → Visualize how categories perform within each region.  
- **Stacked Bars** → Compare total regional revenue and category breakdown.  

### 3. **Store Performance**  
- **Store summary table** (Revenue, Orders, Units).  
- **KPI Trends per store** with period filters (last N months, all-time).  
- **Top Categories / Top Products** for each store.  

### 4. **Inventory Check**  
- **Low-Stock Risk Table** → Identify SKUs at risk of stockouts, flagged by:  
  - Bottom percentile of stock within category.  
  - Coverage below critical threshold (months).  
- **Category Stock Levels Chart** → Coverage vs. sales per category.  
- Download tables as CSV for further analysis.  

### 5. **Customer Analysis**  
- **Top Customers (by revenue)** with category breakdowns.  
- **Cohort Retention Checkpoints** (month 1–4).  
- **Customer Segments:**  
  - New (1 order month)  
  - Repeat (2–4 order months)  
  - Loyal (5+ order months)  

### 6. **About Tab**  
- Data dictionary, metric definitions, SQL methodology.  
- Transparent SQL queries viewable via expanders.  
- Tech stack & deployment notes.  

---

## 🛠️ Tech Stack  

- **Frontend/UI:** Streamlit  
- **Visuals:** Plotly (Express + Graph Objects)  
- **Database:** SQLite (rebuilt automatically from CSVs)  
- **Data Processing:** Pandas  
- **Caching:** Streamlit `@st.cache_resource` and `@st.cache_data`  
- **SQL Storage:** Queries kept in `/queries/*.txt` for version control  

---

## 📂 Project Structure  

