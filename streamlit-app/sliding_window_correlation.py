import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date
from load_data import load_data_from_mongodb, load_data_from_meteo

# Initialize session state for storing results
if 'energy_data' not in st.session_state:
    st.session_state.energy_data = None
if 'weather' not in st.session_state:
    st.session_state.weather = None
if 'selected_city' not in st.session_state:
    st.session_state.selected_city = None
if 'met_var' not in st.session_state:
    st.session_state.met_var = None
if 'energy_var' not in st.session_state:
    st.session_state.energy_var = 'quantitykwh'

# Helper functions
def standardize_datetime(df):
    if "starttime" in df.columns:
        df["starttime"] = pd.to_datetime(df["starttime"])
        df = df.set_index("starttime").sort_index()  
    elif "date" in df.columns:
        df["starttime"] = pd.to_datetime(df["date"])
        df = df.drop("date", axis=1)
        df = df.set_index("starttime").sort_index()

    # Standardizing
    if df.index.tz is None:
        # tz-naive → assume UTC
        df.index = df.index.tz_localize("UTC")
    df.index = df.index.tz_convert("Europe/Oslo") 

    return df

def sliding_window_corr(df, col_x, col_y, window_hours, lag_hours):
        df = df.copy()
        df[col_y + "_lagged"] = df[col_y].shift(lag_hours)
        corr = df[col_x].rolling(f"{window_hours}H").corr(df[col_y + "_lagged"])
        return corr


def sliding_window_correlation():
    st.subheader("Sliding Window Correlation: Energy vs Weather")
    st.write("Please select a range of years where you want to explore the correlation between energy and weather.")
    st.write("Please select for which city in Norway you want to explore the correlation between energy and weather.")
    st.write("Then select which energy group you want to explore.")
    st.write("Then select which meteorological property you want to explore.")
    st.write("Below the query data button you can play with different window lengths and lag for calculating the correlation.")

    try:
        start_year, end_year = st.slider(
            "Select year range:",
            min_value=2021,
            max_value=2024,
            value=(2021, 2024),
            step=1
        )

        cities_list = ["Bergen", "Oslo", "Kristiansand", "Trondheim", "Tromsø"]
        st.session_state.selected_city = st.selectbox(
        "Select a city:",
        options=cities_list
        )

        # Map cities to price area
        cities = {
        'Oslo': "NO1",
        'Kristiansand': "NO2",
        'Trondheim': "NO3",
        'Tromsø': "NO4",    
        'Bergen':"NO5"  
        }

        st.write(f'{st.session_state.selected_city} is in price area {cities[st.session_state.selected_city]}')

        st.session_state.database = st.radio(
            "Select energy dataset",
            ["Production", "Consumption"],
            horizontal=True
        )

        productiongroups = ['hydro', 'other', 'solar', 'thermal', 'wind']
        consumptiongroups = ['cabin', 'household', 'primary', 'secondary', 'tertiary']

        # Select column names depending on selected database
        if st.session_state.database == "Production":
            namespace = "production_NO1"
            groups = productiongroups
            
        else:
            namespace = "consumption_NO1"
            groups = consumptiongroups

        st.session_state.group_selected  = st.selectbox("Select energy group", sorted(groups))

        met_prop = ["temperature_2m", "precipitation", "wind_speed_10m", "wind_gusts_10m", "wind_direction_10m"]
        st.session_state.met_var = st.selectbox("Select a meteorological property:", met_prop)
        st.write(st.session_state.met_var)

        # Query MongoDB and Meteo
        if st.button("Query Data"):
            with st.spinner("Querying data..."):
                st.session_state.energy_data = load_data_from_mongodb(
                    namespace,
                    st.session_state.group_selected,
                    date(start_year, 1, 1),
                    date(end_year, 12, 31)
                )
                
                years = []
                for year in range(start_year, end_year+1):
                    years.append(year)
                data = [load_data_from_meteo(year, st.session_state.selected_city) for year in years]
                st.session_state.weather = pd.concat(data)
                st.success(f"Found {len(st.session_state.weather)+len(st.session_state.energy_data)} records")
                st.write("asdf")
                st.write("Energy data:", len(st.session_state.energy_data))
                st.write("Weather data:", len(st.session_state.weather))
        
        if st.session_state.energy_data is not None and st.session_state.weather is not None:
            
            # Filter on selected price_area or meteorological property
            energy_data = st.session_state.energy_data.copy()
            energy_data = energy_data[energy_data['pricearea']==cities[st.session_state.selected_city]]
            energy_data = energy_data[['starttime', st.session_state.energy_var]]
            weather_data = st.session_state.weather.copy()
            weather_data = weather_data[['date', st.session_state.met_var]]         

            # Standardize datetime
            energy_data = standardize_datetime(energy_data)
            weather_data = standardize_datetime(weather_data)

            # Merge dataframes        
            df_merged = energy_data.merge(
                weather_data, left_index=True, right_index=True, how="inner"
            ).dropna()
            if df_merged.empty:
                st.warning("No overlapping timestamps between weather and energy data.")
                return

            # Set window and lag parameters

            col1, col2 = st.columns(2)
            window = col1.slider("Window length (hours)", 1, 200, 72)
            lag = col2.slider("Lag (hours)", -48, 48, 0)

            # Compute rolling correlation
            corr_series = sliding_window_corr(df_merged, st.session_state.met_var, st.session_state.energy_var, window, lag)

            # Plotting meterological timeseries
            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=energy_data.index,
                y=energy_data[st.session_state.energy_var],
                mode="lines",
                name=f"Plot of selected energy variable ({st.session_state.group_selected})"
            ))
            fig.update_yaxes(title_text=f"{st.session_state.energy_var}")
            fig.update_xaxes(title_text="Time")
            fig.update_layout(height=450, title=f"Plot of selected energy variable ({st.session_state.group_selected})")
            st.plotly_chart(fig, use_container_width=True)
            fig = go.Figure()

            # Plotting meterological timeseries
            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=weather_data.index,
                y=weather_data[st.session_state.met_var],
                mode="lines",
                name=f"Plot of selected meteorological variable ({st.session_state.met_var})"
            ))
            fig.update_yaxes(title_text=f"{st.session_state.met_var}")
            fig.update_xaxes(title_text="Time")
            fig.update_layout(height=450, title=f"Plot of selected meteorological variable ({st.session_state.met_var})")
            st.plotly_chart(fig, use_container_width=True)
            fig = go.Figure()

            # Plotting correlation
            fig.add_trace(go.Scatter(
                x=corr_series.index,
                y=corr_series.values,
                mode="lines",
                name=f"Rolling Corr ({st.session_state.met_var} vs {st.session_state.energy_var})"
            ))
            fig.update_yaxes(title_text="Correlation", range=[-1,1])
            fig.update_xaxes(title_text="Time")
            fig.update_layout(height=450, title=f"Sliding Window Correlation ({st.session_state.met_var} vs {st.session_state.group_selected}) with lag={lag}h, window={window}h")
            st.plotly_chart(fig, use_container_width=True)

        
        else:
            st.info("Please press Query Data to query data and calculate correlations.")

    except Exception as e:
            st.error(f"An error occurred: {str(e)}")

def sliding_window_page():
    sliding_window_correlation()