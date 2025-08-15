import streamlit as st
import pandas as pd
import numpy as np
import time

st.set_page_config(page_title="Bankai", layout="centered")
st.title("Retail Sales Analytics Dashboard")
st.header("Overview")
st.subheader("Welcome to the Retail Sales Analytics Dashboard")
st.write("This dashboard provides insights into retail sales data.")
df = pd.DataFrame({
    'Product': ['A', 'B', 'C', 'D'],
    'Sales': [100, 200, 150, 300],
    'Category': ['Electronics', 'Clothing', 'Electronics', 'Clothing'],
    'Quantity': [1, 2, 1, 3],  
    'Date': pd.date_range(start='2023-01-01', periods=4, freq='D'),
})
st.markdown("> You can use **Markdown** too.")
st.caption("This is a caption for the dashboard.")
st.dataframe(df)
st.divider()
st.line_chart(df)


st.title("Time to start workign with widgets")
name = st.text_input("Enter your name", placeholder="Type here...")
age = st.number_input("Enter a number", min_value=0, max_value=100, value=50)
color = st.selectbox("Select a category", options=df['Category'].unique())
like = st.checkbox("Check this box if you agree")
st.json({"name": name, "age": age, "color": color, "likes_streamlit": like})
st.slider("Select a range", min_value=0, max_value=100, value=50)

st.title("Working with app structure: columns, tabs, and expander")
col1, col2, col3 = st.columns([1, 2, 1])  # Create three columns with different widths
with col1:
    st.write("This is the first column.")
    st.button("Click me!")
with col2:
    st.write("This is the second column.")
    st.selectbox("Choose an option", options=["Option 1", "Option 2", "Option 3"])
with col3:
    st.write("This is the third column.")
    st.text_area("Enter some text here", height=100)

st.header("Tabs now")
tab1, tab2, tab3 = st.tabs(["Tab 1", "Tab 2", "Tab 3"])
with tab1:
    st.write("Content for Tab 1")
    st.line_chart(df['Sales'])
with tab2:
    st.write("Content for Tab 2")
    st.bar_chart(df['Quantity'])    
with tab3:
    with st.expander("Click to expand"):
        st.write("Hidden details")


st.title("Working with control flow: buttons, forms and states")
st.subheader("Button Example")
if st.button("Click me to see a message"):
    with st.spinner("Processing..."):
        time.sleep(2)
    st.success("You clicked the button!")

st.subheader("Form Example")
with st.form("my_form"):
    name = st.text_input("Enter your name")
    age = st.number_input("Enter your age", min_value=0, max_value=120)
    submit_button = st.form_submit_button("Submit")
    if submit_button:
        st.write(f"Hello {name}, you are {age} years old!")

st.subheader("State Example")
if 'count' not in st.session_state:
    st.session_state.count = 0
if st.button("Increment Count"):
    st.session_state.count += 1
st.write(f"Current count: {st.session_state.count}")

## Working with data: loading, displaying, and manipulating data. Work on this later
st.title("Working with data: loading, displaying, and manipulating data")

st.title("Uploading csv files")
uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.write("DataFrame loaded from CSV:")
    st.dataframe(df)

#caching data
@st.cache_data
def load_data():
    # Simulate a data loading process
    time.sleep(2)
    return pd.DataFrame({
        'A': [1, 21, 3],
        'B': [4, 5, 6],
        'C': [7, 8, 9]
    })

st.dataframe(load_data())