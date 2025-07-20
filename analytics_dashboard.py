import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import analytics

# Page configuration
st.set_page_config(
    page_title="Dashboard Analytics",
    page_icon="📊",
    layout="wide"
)

# Header
st.title("Stock Market Dashboard Analytics")
st.markdown("---")

# Initialize analytics for tracking visits to the analytics dashboard itself
analytics.initialize_analytics()
analytics.record_page_view("Analytics Dashboard")

# Display tabs for different analytics views
tab1, tab2, tab3 = st.tabs(["User Engagement", "Feature Usage", "Performance"])

with tab1:
    st.header("User Engagement")
    
    # Load analytics data
    analytics_data = analytics.load_analytics_data()
    
    # Check if data exists
    if not analytics_data.get("visits"):
        st.info("No analytics data available yet. Start using the dashboard to generate analytics.")
    else:
        # Convert lists to DataFrames for processing
        visits_df = pd.DataFrame(analytics_data.get("visits", []))
        page_views_df = pd.DataFrame(analytics_data.get("page_views", []))
        
        # Process datetime
        if not visits_df.empty:
            visits_df["datetime"] = pd.to_datetime(visits_df["timestamp"])
            visits_df["date"] = visits_df["datetime"].dt.date
        
        if not page_views_df.empty:
            page_views_df["datetime"] = pd.to_datetime(page_views_df["timestamp"])
            page_views_df["date"] = page_views_df["datetime"].dt.date
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Sessions", len(visits_df))
        
        with col2:
            unique_users = len(visits_df["user_id"].unique()) if not visits_df.empty else 0
            st.metric("Unique Users", unique_users)
        
        with col3:
            if not page_views_df.empty:
                avg_views = page_views_df.groupby("user_id").size().mean()
                st.metric("Avg. Views Per User", f"{avg_views:.1f}")
            else:
                st.metric("Avg. Views Per User", "0")
        
        with col4:
            if not visits_df.empty:
                today = datetime.now().date()
                today_visits = len(visits_df[visits_df["date"] == today])
                st.metric("Today's Visits", today_visits)
            else:
                st.metric("Today's Visits", "0")
        
        # Visits over time
        if not visits_df.empty:
            st.subheader("Daily Visits")
            
            # Group by day and count visits
            visits_by_day = visits_df.groupby("date").size().reset_index()
            visits_by_day.columns = ["date", "visits"]
            
            # Create line chart
            fig = px.line(
                visits_by_day, 
                x="date", 
                y="visits",
                labels={"date": "Date", "visits": "Number of Visits"},
                markers=True
            )
            
            # Update layout
            fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Visits",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Page popularity
        if not page_views_df.empty:
            st.subheader("Page Popularity")
            
            # Group by page and count views
            page_popularity = page_views_df.groupby("page_name").size().reset_index()
            page_popularity.columns = ["page_name", "views"]
            page_popularity = page_popularity.sort_values("views", ascending=False)
            
            # Create bar chart
            fig = px.bar(
                page_popularity,
                x="page_name",
                y="views",
                labels={"page_name": "Page", "views": "Views"},
                color="views",
                color_continuous_scale=px.colors.sequential.Blues
            )
            
            # Update layout
            fig.update_layout(
                xaxis_title="Page",
                yaxis_title="Number of Views",
                coloraxis_showscale=False,
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.header("Feature Usage")
    
    # Load analytics data
    analytics_data = analytics.load_analytics_data()
    
    # Check if data exists
    if not analytics_data.get("interactions"):
        st.info("No interaction data available yet.")
    else:
        # Convert to DataFrame
        interactions_df = pd.DataFrame(analytics_data.get("interactions", []))
        
        if not interactions_df.empty:
            # Process datetime
            interactions_df["datetime"] = pd.to_datetime(interactions_df["timestamp"])
            
            # Interaction types
            st.subheader("Feature Usage Distribution")
            
            # Group by interaction type and count
            interaction_types = interactions_df.groupby("interaction_type").size().reset_index()
            interaction_types.columns = ["interaction_type", "count"]
            interaction_types = interaction_types.sort_values("count", ascending=False)
            
            # Create charts
            col1, col2 = st.columns([3, 2])
            
            with col1:
                # Bar chart
                fig = px.bar(
                    interaction_types,
                    x="interaction_type",
                    y="count",
                    labels={"interaction_type": "Interaction Type", "count": "Count"},
                    color="count",
                    color_continuous_scale=px.colors.sequential.Viridis
                )
                
                # Update layout
                fig.update_layout(
                    xaxis_title="Feature/Interaction",
                    yaxis_title="Usage Count",
                    coloraxis_showscale=False,
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Pie chart
                fig = px.pie(
                    interaction_types,
                    values="count",
                    names="interaction_type",
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                
                # Update layout
                fig.update_layout(
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            # Stock selection analysis
            stock_selections = interactions_df[interactions_df["interaction_type"] == "stock_selection"]
            if not stock_selections.empty:
                st.subheader("Most Popular Stocks")
                
                # Extract stock selections from details field
                stock_counts = {}
                for _, row in stock_selections.iterrows():
                    details = row.get("details", {})
                    if isinstance(details, dict) and "stocks" in details:
                        stocks = details["stocks"]
                        if isinstance(stocks, list):
                            for stock in stocks:
                                if stock in stock_counts:
                                    stock_counts[stock] += 1
                                else:
                                    stock_counts[stock] = 1
                
                if stock_counts:
                    # Convert to DataFrame
                    stock_df = pd.DataFrame([
                        {"stock": stock, "count": count}
                        for stock, count in stock_counts.items()
                    ]).sort_values("count", ascending=False)
                    
                    # Create bar chart
                    fig = px.bar(
                        stock_df,
                        x="stock",
                        y="count",
                        labels={"stock": "Stock Symbol", "count": "Selection Count"},
                        color="count",
                        color_continuous_scale=px.colors.sequential.Reds
                    )
                    
                    # Update layout
                    fig.update_layout(
                        xaxis_title="Stock",
                        yaxis_title="Times Selected",
                        coloraxis_showscale=False,
                        height=400
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
            
            # Time period analysis
            time_period_changes = interactions_df[interactions_df["interaction_type"] == "time_period_change"]
            if not time_period_changes.empty:
                st.subheader("Most Used Time Periods")
                
                # Extract time periods from details field
                period_counts = {}
                for _, row in time_period_changes.iterrows():
                    details = row.get("details", {})
                    if isinstance(details, dict) and "period" in details:
                        period = details["period"]
                        if period in period_counts:
                            period_counts[period] += 1
                        else:
                            period_counts[period] = 1
                
                if period_counts:
                    # Convert to DataFrame
                    period_df = pd.DataFrame([
                        {"period": period, "count": count}
                        for period, count in period_counts.items()
                    ]).sort_values("count", ascending=False)
                    
                    # Create horizontal bar chart
                    fig = px.bar(
                        period_df,
                        y="period",
                        x="count",
                        labels={"period": "Time Period", "count": "Usage Count"},
                        orientation='h',
                        color="count",
                        color_continuous_scale=px.colors.sequential.Greens
                    )
                    
                    # Update layout
                    fig.update_layout(
                        yaxis_title="Time Period",
                        xaxis_title="Usage Count",
                        coloraxis_showscale=False,
                        height=400
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.header("Performance Analytics")
    
    # Load analytics data
    analytics_data = analytics.load_analytics_data()
    
    # Check if interaction data exists
    if not analytics_data.get("interactions"):
        st.info("No performance data available yet.")
    else:
        # Convert to DataFrame
        interactions_df = pd.DataFrame(analytics_data.get("interactions", []))
        
        if not interactions_df.empty:
            # Process datetime
            interactions_df["datetime"] = pd.to_datetime(interactions_df["timestamp"])
            
            # Focus on data fetch interactions
            data_fetches = interactions_df[interactions_df["interaction_type"] == "data_fetch"]
            if not data_fetches.empty:
                st.subheader("Data Fetch Distribution by Stock")
                
                # Extract stock symbols from details field
                ticker_counts = {}
                for _, row in data_fetches.iterrows():
                    details = row.get("details", {})
                    if isinstance(details, dict) and "ticker" in details:
                        ticker = details["ticker"]
                        if ticker in ticker_counts:
                            ticker_counts[ticker] += 1
                        else:
                            ticker_counts[ticker] = 1
                
                if ticker_counts:
                    # Convert to DataFrame
                    ticker_df = pd.DataFrame([
                        {"ticker": ticker, "count": count}
                        for ticker, count in ticker_counts.items()
                    ]).sort_values("count", ascending=False)
                    
                    # Create treemap
                    fig = px.treemap(
                        ticker_df,
                        path=["ticker"],
                        values="count",
                        color="count",
                        color_continuous_scale=px.colors.sequential.Blues_r,
                        title="Data Fetches by Stock"
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
            
            # Dashboard updates and refreshes
            updates = interactions_df[interactions_df["interaction_type"].isin(["dashboard_update", "dashboard_auto_refresh"])]
            if not updates.empty:
                st.subheader("Dashboard Updates Over Time")
                
                # Group by hour and type
                updates["hour"] = updates["datetime"].dt.floor("H")
                update_counts = updates.groupby(["hour", "interaction_type"]).size().reset_index()
                update_counts.columns = ["hour", "update_type", "count"]
                
                # Create line chart
                fig = px.line(
                    update_counts,
                    x="hour",
                    y="count",
                    color="update_type",
                    labels={"hour": "Hour", "count": "Number of Updates", "update_type": "Update Type"},
                    markers=True
                )
                
                # Update layout
                fig.update_layout(
                    xaxis_title="Time",
                    yaxis_title="Updates",
                    height=400,
                    legend_title="Update Type"
                )
                
                st.plotly_chart(fig, use_container_width=True)

# Raw data section
with st.expander("View Raw Analytics Data"):
    analytics_data = analytics.load_analytics_data()
    
    st.subheader("Visits")
    visits_df = pd.DataFrame(analytics_data.get("visits", []))
    if not visits_df.empty:
        st.dataframe(visits_df, hide_index=True)
    else:
        st.info("No visit data available.")
    
    st.subheader("Page Views")
    page_views_df = pd.DataFrame(analytics_data.get("page_views", []))
    if not page_views_df.empty:
        st.dataframe(page_views_df, hide_index=True)
    else:
        st.info("No page view data available.")
    
    st.subheader("Interactions")
    interactions_df = pd.DataFrame(analytics_data.get("interactions", []))
    if not interactions_df.empty:
        st.dataframe(interactions_df, hide_index=True)
    else:
        st.info("No interaction data available.") 