import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import os

sns.set(style='dark')

# Load data
@st.cache_data
def load_data():
    try:
        # Check both potential paths
        if os.path.exists("dashboard/main_data.csv"):
            return pd.read_csv("dashboard/main_data.csv")
        elif os.path.exists("main_data.csv"):
            return pd.read_csv("main_data.csv")
        else:
            return None
    except Exception as e:
        return None

# Helper function for binning (Advanced Analysis)
def categorize_pm25(pm):
    if pm <= 50:
        return 'Good'
    elif pm <= 100:
        return 'Moderate'
    elif pm <= 150:
        return 'Unhealthy for Sensitive Groups'
    else:
        return 'Unhealthy'

# Header
st.header('Air Quality Dashboard')

# Load data
all_df = load_data()

if all_df is None:
    st.error("Data not found. Please run the data generation script or ensure 'main_data.csv' is available.")
else:
    # Preprocess
    all_df['date'] = pd.to_datetime(all_df['date'])
    
    # Calculate Category if not present (Ensures backward compatibility)
    if 'Air_Quality_Category' not in all_df.columns:
        all_df['Air_Quality_Category'] = all_df['PM2.5'].apply(categorize_pm25)

    # Sidebar
    with st.sidebar:
        st.title("Air Quality Beijing")
        
        # Station Filter
        station_list = all_df['station'].unique().tolist()
        selected_station = st.multiselect(
            label="Select Station",
            options=station_list,
            default=[station_list[0]]
        )
        
        # Date Filter
        min_date = all_df['date'].min()
        max_date = all_df['date'].max()
        
        start_date, end_date = st.date_input(
            label='Time Range',
            min_value=min_date,
            max_value=max_date,
            value=[min_date, max_date]
        )

    # Filter data
    main_df = all_df[(all_df["date"] >= str(start_date)) & 
                     (all_df["date"] <= str(end_date))]
    
    if selected_station:
        main_df = main_df[main_df['station'].isin(selected_station)]

    # Metrics
    col1, col2 = st.columns(2)
    with col1:
        avg_pm25 = main_df['PM2.5'].mean()
        st.metric("Avg PM2.5", value=f"{avg_pm25:.2f}")
    with col2:
        avg_pm10 = main_df['PM10'].mean()
        st.metric("Avg PM10", value=f"{avg_pm10:.2f}")

    # Plot 1: Daily Trend
    st.subheader("Daily PM2.5 Levels Trend")
    daily_df = main_df.resample(rule='D', on='date').agg({
        "PM2.5": "mean",
    }).reset_index()
    
    fig, ax = plt.subplots(figsize=(16, 8))
    ax.plot(daily_df["date"], daily_df["PM2.5"], linewidth=2, color="#90CAF9")
    ax.set_ylabel("PM2.5 Concentration")
    ax.tick_params(axis='y', labelsize=15)
    ax.tick_params(axis='x', labelsize=15)
    st.pyplot(fig)

    # Plot 2: Pollutant Comparison by Station
    st.subheader("Average Pollutant Levels by Station")
    if len(selected_station) > 0:
        station_avg = main_df.groupby('station')[['PM2.5', 'PM10', 'SO2', 'NO2']].mean().reset_index()
        station_melt = station_avg.melt(id_vars='station', var_name='Pollutant', value_name='Concentration')
        
        fig2, ax2 = plt.subplots(figsize=(12, 6))
        sns.barplot(x='station', y='Concentration', hue='Pollutant', data=station_melt, ax=ax2)
        ax2.set_xlabel("Station", fontsize=15)
        ax2.set_ylabel("Concentration", fontsize=15)
        plt.xticks(rotation=45)
        st.pyplot(fig2)
    else:
        st.info("Select stations to compare.")

    # Advanced Analysis: Air Quality Category Distribution
    st.subheader("Advanced Analysis: Air Quality Categories (Binning)")
    
    category_counts = main_df['Air_Quality_Category'].value_counts()
    
    col_pie, col_desc = st.columns([2, 1])
    
    with col_pie:
        fig3, ax3 = plt.subplots(figsize=(8, 8))
        ax3.pie(category_counts, labels=category_counts.index, autopct='%1.1f%%', startangle=140, colors=sns.color_palette('pastel'))
        ax3.set_title('Distribution of Air Quality (PM2.5)')
        st.pyplot(fig3)
    
    with col_desc:
        st.markdown("""
        **Categories:**
        - **Good**: PM2.5 ≤ 50
        - **Moderate**: 50 < PM2.5 ≤ 100
        - **Unhealthy for Sensitive Groups**: 100 < PM2.5 ≤ 150
        - **Unhealthy**: PM2.5 > 150
        """)

    st.caption('Dicoding Air Quality Analysis Project')
