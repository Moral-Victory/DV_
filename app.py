import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
import json
import time
from datetime import datetime

# Set page configuration
st.set_page_config(
    page_title="Predictive Maintenance Dashboard",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
.main {
    background-color: #1E1E3F;
    color: white;
}
.stApp {
    background-color: #1E1E3F;
}
div[data-testid="stSidebar"] {
    background-color: #2D2D5D;
}
.st-bq {
    background-color: #2D2D5D;
}
div[data-testid="stMetric"] {
    background-color: #2D2D5D;
    border-radius: 10px;
    padding: 15px;
    margin: 10px 0;
}
.metric-container {
    background-color: #2D2D5D;
    border-radius: 10px;
    padding: 15px;
    margin: 10px 0;
}
.failure-0 {
    color: #4CAF50;
}
.failure-1 {
    color: #F44336;
}
.title {
    font-size: 30px;
    font-weight: bold;
    text-align: center;
    margin-bottom: 20px;
    color: white;
}
</style>
""", unsafe_allow_html=True)

# API base URL - change this if your API is running on a different host/port
API_URL = "http://localhost:8000"

# Title
st.markdown("<div class='title'>Predictive Maintenance Dashboard</div>", unsafe_allow_html=True)

# Sidebar for controls
with st.sidebar:
    st.header("Controls")
    
    # Generate synthetic data
    st.subheader("Generate Data")
    data_count = st.slider("Number of data points", 10, 10000, 100)
    if st.button("Generate Data"):
        with st.spinner("Generating data..."):
            try:
                response = requests.post(f"{API_URL}/generate_data?count={data_count}")
                if response.status_code == 200:
                    st.success(f"Generated {data_count} data points")
                else:
                    st.error(f"Failed to generate data: {response.text}")
            except requests.exceptions.ConnectionError:
                st.error(f"Could not connect to API at {API_URL}. Make sure the FastAPI server is running.")
    
    # Clear data
    st.subheader("Clear Data")
    if st.button("Clear All Data"):
        with st.spinner("Clearing data..."):
            try:
                response = requests.delete(f"{API_URL}/clear_data")
                if response.status_code == 200:
                    st.success("All data cleared")
                else:
                    st.error(f"Failed to clear data: {response.text}")
            except requests.exceptions.ConnectionError:
                st.error(f"Could not connect to API at {API_URL}. Make sure the FastAPI server is running.")
    
    # Manual prediction
    st.subheader("Test Prediction")
    with st.form("prediction_form"):
        machine_type = st.selectbox("Product Quality Type", [0, 1, 2], format_func=lambda x: f"Type {x}")
        air_temp = st.slider("Air Temperature [K]", 295.0, 304.0, 298.0, 0.1)
        process_temp = st.slider("Process Temperature [K]", 305.0, 313.0, 308.0, 0.1)
        rotational_speed = st.slider("Rotational Speed [rpm]", 1000, 2500, 1500)
        torque = st.slider("Torque [Nm]", 3.5, 77.0, 40.0, 0.1)
        tool_wear = st.slider("Tool Wear [min]", 0, 253, 100)
        
        submit_button = st.form_submit_button("Predict")
        
        if submit_button:
            data = {
                "Type": machine_type,
                "Air_temperature_K": air_temp,
                "Process_temperature_K": process_temp,
                "Rotational_speed_rpm": rotational_speed,
                "Torque_Nm": torque,
                "Tool_wear_min": tool_wear
            }
            
            try:
                response = requests.post(f"{API_URL}/predict", json=data)
                
                if response.status_code == 200:
                    result = response.json()
                    prediction = result["prediction"]
                    failure = "Yes" if prediction == 0 else "No"
                    color_class = "failure-1" if prediction == 1 else "failure-0"
                    
                    st.markdown(f"""
                    <div class='metric-container'>
                        <h3>Prediction Result</h3>
                        <p>Machine Failure: <span class='{color_class}'>{failure}</span></p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error(f"Prediction failed: {response.text}")
            except requests.exceptions.ConnectionError:
                st.error(f"Could not connect to API at {API_URL}. Make sure the FastAPI server is running.")

# Function to fetch data from API
@st.cache_data(ttl=5)  # Cache data for 5 seconds
def get_data():
    try:
        response = requests.get(f"{API_URL}/data")
        if response.status_code == 200:
            data = response.json()["data"]
            if data:
                return pd.DataFrame(data)
            else:
                return pd.DataFrame()
        else:
            st.error(f"Failed to fetch data: {response.text}")
            return pd.DataFrame()
    except requests.exceptions.ConnectionError:
        st.error(f"Could not connect to API at {API_URL}. Make sure the FastAPI server is running.")
        return pd.DataFrame()

# Get data
df = get_data()
st.write(f"Fetched {len(df)} rows")
# Main dashboard
if df.empty:
    st.info("No data available. Generate some data using the sidebar controls.")
else:
    # Create metrics and visualizations
    col1, col2, col3 = st.columns(3)
    
    with col1:
        max_torque = df["Torque [Nm]"].max()
        st.markdown(f"""
        <div class='metric-container'>
            <h3>Max of Torque [Nm]</h3>
            <p style='font-size: 32px; text-align: center;'>{max_torque:.2f}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        max_tool_wear = df["Tool wear [min]"].max()
        st.markdown(f"""
        <div class='metric-container'>
            <h3>Max of Tool wear [min]</h3>
            <p style='font-size: 32px; text-align: center;'>{max_tool_wear:.0f}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        avg_rotational_speed = df["Rotational speed [rpm]"].mean()
        st.markdown(f"""
        <div class='metric-container'>
            <h3>Average of Rotational speed [rpm]</h3>
            <p style='font-size: 32px; text-align: center;'>{avg_rotational_speed:.2f}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Create graphs
    col1, col2 = st.columns(2)
    
    with col1:
        # Machine Failure Count
        failure_counts = df["prediction"].value_counts().reset_index()
        failure_counts.columns = ["Failure", "Count"]
        
        fig = px.bar(
            failure_counts,
            x="Failure",
            y="Count",
            color="Failure",
            color_discrete_sequence=["#3498db", "#e74c3c"],
            title="Machine Failure Count",
            labels={"Count": "Count","Failure": "Target"},
        )
        fig.update_layout(
            plot_bgcolor="#2D2D5D",
            paper_bgcolor="#2D2D5D",
            font=dict(color="white"),
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Count of Type by Type
        type_counts = df["Type"].value_counts().reset_index()
        type_counts.columns = ["Type", "Count"]
        
        fig = px.pie(
            type_counts,
            values="Count",
            names="Type",
            title="Count of Product Quality Type",
            color_discrete_sequence=px.colors.qualitative.Set3,
        )
        fig.update_layout(
            plot_bgcolor="#2D2D5D",
            paper_bgcolor="#2D2D5D",
            font=dict(color="white"),
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Count of Type by Target and Failure Type
        type_target_counts = df.groupby(["Type", "prediction"]).size().reset_index(name="Count")
        
        fig = px.bar(
            type_target_counts,
            x="prediction",
            y="Count",
            color="Type",
            barmode="group",
            title="Count of Product Quality Type and Target",
            labels={"prediction": "Target", "Count": "Count of Product Quality Type", "Type": "Product Quality Type"},
            color_discrete_sequence=px.colors.qualitative.Set3,
        )
        fig.update_layout(
            plot_bgcolor="#2D2D5D",
            paper_bgcolor="#2D2D5D",
            font=dict(color="white"),
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Count of Target by Target
        target_counts = df["prediction"].value_counts(normalize=True).reset_index()
        target_counts.columns = ["Target", "Percentage"]
        target_counts["Percentage"] = target_counts["Percentage"] * 100
        
        fig = px.pie(
            target_counts,
            values="Percentage",
            names="Target",
            title="Count of Target by Target",
            color_discrete_sequence=["#3498db", "#e74c3c"],
        )
        fig.update_layout(
            plot_bgcolor="#2D2D5D",
            paper_bgcolor="#2D2D5D",
            font=dict(color="white"),
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Create bottom row graphs
    # col1, col2, col3 = st.columns(3)
    col2, col3 = st.columns(2)
    
    # with col1:
    #     # Count by Type
    #     type_failure_counts = df.groupby(["Type", "prediction"]).size().reset_index(name="Count")
        
    #     fig = px.bar(
    #         type_failure_counts,
    #         x="prediction",
    #         y="Count",
    #         color="Type",
    #         facet_col="Type",
    #         title="Count by Type",
    #         labels={"prediction": "Failure", "Count": "Count"},
    #         color_discrete_sequence=px.colors.qualitative.Set3,
    #     )
    #     fig.update_layout(
    #         plot_bgcolor="#2D2D5D",
    #         paper_bgcolor="#2D2D5D",
    #         font=dict(color="white"),
    #     )
    #     st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Air Temp v/s Rotational Speed
        df_sample = df.sample(min(len(df), 500))
        
        fig = px.scatter(
            df_sample,
            x="Rotational speed [rpm]",
            y="Air temperature [K]",
            title="Air Temp v/s Rotational Speed",
            color="prediction",
            color_discrete_sequence=["#3498db", "#e74c3c"],
            opacity=0.7,
        )
        fig.update_layout(
            plot_bgcolor="#2D2D5D",
            paper_bgcolor="#2D2D5D",
            font=dict(color="white"),
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col3:
        # Process Temp v/s Rotational Speed
        fig = px.scatter(
            df_sample,
            x="Rotational speed [rpm]",
            y="Process temperature [K]",
            title="Process Temp v/s Rotational Speed",
            color="prediction",
            color_discrete_sequence=["#3498db", "#e74c3c"],
            opacity=0.7,
        )
        fig.update_layout(
            plot_bgcolor="#2D2D5D",
            paper_bgcolor="#2D2D5D",
            font=dict(color="white"),
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Display raw data (collapsible)
    with st.expander("View Raw Data"):
        st.dataframe(df.head(100).style.background_gradient(cmap='viridis', subset=["Tool wear [min]", "Torque [Nm]"]))