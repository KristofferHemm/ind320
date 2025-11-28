import streamlit as st
import pandas as pd
import snowdrift_utilities as sd
from load_data import load_data_from_meteo_snow

# Initialize session state for storing results
if 'weather_data' not in st.session_state:
    st.session_state.weather_data = None

def state_checker():

    st.subheader("Snowdrift calculation and illustration")
    st.write("The snowdrift will be calculated for the location you picked on the map on the previuos page.")
    st.write("Please select the desired range of years you want to calculate snow drift.")

    # Check if latitude and longitude has bben selected
    if st.session_state.get("clicked_lat") is None or st.session_state.get("clicked_lon") is None :
        st.warning("Please select a location on the map page before calculating snow drift.")
        return
    
    st.write(f"Latitude: {st.session_state.clicked_lat:.6f}")
    st.write(f"Longitude: {st.session_state.clicked_lon:.6f}")

def calculate_snowdrift():

    # Year range selection
    start_year, end_year = st.slider(
        "Select year range",
        min_value=2015,
        max_value=2023,
        value=(2022, 2023),
        step=1
    )

    years = list(range(start_year, end_year+2))

    # Query Meteo
    if st.button("Query Data"):
        with st.spinner("Querying Meteo API..."):
            data = [load_data_from_meteo_snow(year) for year in years]
            st.session_state.weather_data = pd.concat(data)
            st.success(f"Found {len(st.session_state.weather_data)} records")
            

    if st.session_state.weather_data is not None:
        # Extract month from date column
        st.session_state.weather_data['date'] = (st.session_state.weather_data['date'].dt.tz_localize(None))
        st.session_state.weather_data['date'] = pd.to_datetime(st.session_state.weather_data['date'])
        st.session_state.weather_data['month'] = st.session_state.weather_data['date'].dt.month
        
        # Define season: if month >= 7, season = current year; otherwise, season = previous year.
        st.session_state.weather_data['season'] = st.session_state.weather_data['date'].apply(lambda dt: dt.year if dt.month >= 7 else dt.year - 1)

        # Parameters for the snow transport calculation.
        T = 3000      # Maximum transport distance in meters
        F = 30000     # Fetch distance in meters
        theta = 0.5   # Relocation coefficient


        # Compute seasonal results (yearly averages for each season).
        yearly_df = sd.compute_yearly_results(st.session_state.weather_data, T, F, theta)
        overall_avg = yearly_df['Qt (kg/m)'].mean()
        st.write(f"Overall average Qt over all seasons: {overall_avg / 1000:.1f} tonnes/m")
        
        yearly_df_disp = yearly_df.copy()
        yearly_df_disp["Qt (tonnes/m)"] = yearly_df_disp["Qt (kg/m)"] / 1000
        #st.write("\nYearly average snow drift (Qt) per season (in tonnes/m) and control type:")
        #st.write(yearly_df_disp[['season', 'Qt (tonnes/m)', 'Control']].to_string(index=False, 
        #      formatters={'Qt (tonnes/m)': lambda x: f"{x:.1f}"}))
        
        overall_avg_tonnes = overall_avg / 1000
        st.write(f"\nOverall average Qt over all seasons: {overall_avg_tonnes:.1f} tonnes/m")
        
        # Compute the average directional breakdown (average over all seasons).
        avg_sectors = sd.compute_average_sector(st.session_state.weather_data)
        
        # Create the rose plot canvas with the average directional breakdown.
        fig = sd.plot_rose_plotly(avg_sectors, overall_avg)
        st.plotly_chart(fig, use_container_width=True)
        
        

def snowdrift_page():
    state_checker()
    calculate_snowdrift()