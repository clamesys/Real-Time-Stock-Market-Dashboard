import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from datetime import datetime, timedelta
import os
import uuid

# File to store analytics data
ANALYTICS_FILE = "analytics_data.json"

def initialize_analytics():
    """Initialize analytics in session state if not already present"""
    if 'analytics_initialized' not in st.session_state:
        st.session_state.analytics_initialized = True
        st.session_state.user_id = str(uuid.uuid4())
        st.session_state.visit_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.session_state.page_views = {}
        st.session_state.interactions = []
        
        # Record visit
        record_visit()

def record_visit():
    """Record a new visit to the dashboard"""
    visit_data = {
        "user_id": st.session_state.user_id,
        "timestamp": st.session_state.visit_timestamp,
        "session_id": str(uuid.uuid4())
    }
    
    # Load existing data
    all_analytics = load_analytics_data()
    
    # Append new visit
    if "visits" not in all_analytics:
        all_analytics["visits"] = []
    all_analytics["visits"].append(visit_data)
    
    # Save updated data
    save_analytics_data(all_analytics)
    
def record_page_view(page_name):
    """Record a page view"""
    if page_name not in st.session_state.page_views:
        st.session_state.page_views[page_name] = 0
    
    st.session_state.page_views[page_name] += 1
    
    page_view_data = {
        "user_id": st.session_state.user_id,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "page_name": page_name,
        "view_count": st.session_state.page_views[page_name]
    }
    
    # Load existing data
    all_analytics = load_analytics_data()
    
    # Append new page view
    if "page_views" not in all_analytics:
        all_analytics["page_views"] = []
    all_analytics["page_views"].append(page_view_data)
    
    # Save updated data
    save_analytics_data(all_analytics)

def record_interaction(interaction_type, details=None):
    """Record a user interaction"""
    interaction_data = {
        "user_id": st.session_state.user_id,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "interaction_type": interaction_type,
        "details": details or {}
    }
    
    st.session_state.interactions.append(interaction_data)
    
    # Load existing data
    all_analytics = load_analytics_data()
    
    # Append new interaction
    if "interactions" not in all_analytics:
        all_analytics["interactions"] = []
    all_analytics["interactions"].append(interaction_data)
    
    # Save updated data
    save_analytics_data(all_analytics)

def load_analytics_data():
    """Load analytics data from file"""
    if not os.path.exists(ANALYTICS_FILE):
        return {"visits": [], "page_views": [], "interactions": []}
    
    try:
        with open(ANALYTICS_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {"visits": [], "page_views": [], "interactions": []}

def save_analytics_data(data):
    """Save analytics data to file"""
    with open(ANALYTICS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def display_analytics_dashboard():
    """Display analytics dashboard"""
    st.title("Dashboard Analytics")
    
    # Load analytics data
    analytics_data = load_analytics_data()
    
    if not analytics_data.get("visits"):
        st.info("No analytics data available yet.")
        return
    
    # Convert lists to DataFrames for easier processing
    visits_df = pd.DataFrame(analytics_data.get("visits", []))
    page_views_df = pd.DataFrame(analytics_data.get("page_views", []))
    interactions_df = pd.DataFrame(analytics_data.get("interactions", []))
    
    # Add datetime column for time-based analysis
    if not visits_df.empty:
        visits_df["datetime"] = pd.to_datetime(visits_df["timestamp"])
    if not page_views_df.empty:
        page_views_df["datetime"] = pd.to_datetime(page_views_df["timestamp"])
    if not interactions_df.empty:
        interactions_df["datetime"] = pd.to_datetime(interactions_df["timestamp"])
    
    # Display key metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Visits", len(visits_df))
    
    with col2:
        unique_users = len(visits_df["user_id"].unique()) if not visits_df.empty else 0
        st.metric("Unique Users", unique_users)
    
    with col3:
        total_interactions = len(interactions_df) if not interactions_df.empty else 0
        st.metric("Total Interactions", total_interactions)
    
    # Visits over time
    st.subheader("Visits Over Time")
    
    if not visits_df.empty:
        # Group by day and count visits
        visits_by_day = visits_df.groupby(visits_df["datetime"].dt.date).size().reset_index()
        visits_by_day.columns = ["date", "visits"]
        
        # Create line chart
        fig = px.line(
            visits_by_day, 
            x="date", 
            y="visits",
            title="Daily Visits",
            labels={"date": "Date", "visits": "Number of Visits"}
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No visit data available.")
    
    # Page popularity
    st.subheader("Page Popularity")
    
    if not page_views_df.empty:
        # Group by page and count views
        page_popularity = page_views_df.groupby("page_name").size().reset_index()
        page_popularity.columns = ["page_name", "views"]
        page_popularity = page_popularity.sort_values("views", ascending=False)
        
        # Create bar chart
        fig = px.bar(
            page_popularity,
            x="page_name",
            y="views",
            title="Page Views",
            labels={"page_name": "Page", "views": "Views"}
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No page view data available.")
    
    # Interaction types
    st.subheader("Interaction Types")
    
    if not interactions_df.empty:
        # Group by interaction type and count
        interaction_types = interactions_df.groupby("interaction_type").size().reset_index()
        interaction_types.columns = ["interaction_type", "count"]
        interaction_types = interaction_types.sort_values("count", ascending=False)
        
        # Create pie chart
        fig = px.pie(
            interaction_types,
            values="count",
            names="interaction_type",
            title="Interaction Distribution"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No interaction data available.")
    
    # Raw data tables (expandable)
    with st.expander("Raw Analytics Data"):
        st.subheader("Visits")
        st.dataframe(visits_df)
        
        st.subheader("Page Views")
        st.dataframe(page_views_df)
        
        st.subheader("Interactions")
        st.dataframe(interactions_df) 