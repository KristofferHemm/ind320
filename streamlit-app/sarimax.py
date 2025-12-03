import streamlit as st
import pandas as pd
import statsmodels.api as sm
import plotly.express as px
import plotly.graph_objects as go
from datetime import date
from load_data import load_data_from_mongodb

def sarimax():

    # Initialize session state for storing results
    if 'df' not in st.session_state:
        st.session_state.df = None
    if 'selected_city' not in st.session_state:
        st.session_state.selected_city = None
    if 'selected_pricearea' not in st.session_state:
        st.session_state.selected_pricearea = None

    st.subheader("Forecasting of energy production and consumption")
    st.write("Model used: SARIMAX")
    st.write("Please select which data you want to see below, then click the Query Data button to load data into the plots.")
    st.write("When the data is loaded you can set the SARIMAX parameters below and press Run SARIMAX Forecast")

    # Select timeframe for training and forecast
    #st.write("Select Time Interval")
    col1, col2 = st.columns(2)

    with col1:
        from_date = st.date_input(
            "Choose training window start date",
            value=date(2021, 1, 1),
            min_value=date(2021, 1, 1),
            max_value=date(2024, 12, 31)
        )

    with col2:
        to_date = st.date_input(
            "Choose training window end date",
            value=date(2024, 12, 31),
            min_value=date(2021, 1, 1),
            max_value=date(2024, 12, 31)
        )

    # Select city 
    cities = ["Bergen", "Oslo", "Kristiansand", "Trondheim", "Tromsø"]
    st.session_state.selected_city = st.selectbox(
    "Select a city:",
    options=cities
    )

    # Map cities to price area
    cities = {
    'Oslo': "NO1",
    'Kristiansand': "NO2",
    'Trondheim': "NO3",
    'Tromsø': "NO4",    
    'Bergen':"NO5"  
    }

    st.session_state.selected_pricearea = cities[st.session_state.selected_city]
    st.write(f'{st.session_state.selected_city} is in price area {st.session_state.selected_pricearea}')

    # Select production/consumption    
    st.session_state.database = st.radio(
        "Dataset",
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

    st.session_state.group_selected  = st.selectbox("Select group", sorted(groups))

    # Query MongoDB
    if st.button("Query Data"):
        if from_date > to_date:
            st.error("Error: 'From date' must be before 'To date'")
        elif not st.session_state.group_selected :
            st.error("Please enter a group name")
        else:
            with st.spinner("Querying database..."):
                st.session_state.df = load_data_from_mongodb(
                    namespace,
                    st.session_state.group_selected,
                    from_date,
                    to_date
                )

                # Subset the dataframe for selected price area
                st.session_state.df = st.session_state.df[st.session_state.df['pricearea'] == st.session_state.selected_pricearea]
                st.success(f"Found {len(st.session_state.df)} records")
    
    # Only process the dataframe if it exists
    if st.session_state.df is not None:

        # Ensure starttime is in datetime format
        st.session_state.df['starttime'] = pd.to_datetime(st.session_state.df['starttime'])

        # Group by date and sum quantitykwh
        st.session_state.df = st.session_state.df.groupby(st.session_state.df['starttime'].dt.date)['quantitykwh'].sum().reset_index()

        # Setting parameters
        st.subheader("SARIMAX Parameters")

        forecast_days = st.number_input("Type in number of days to forecast. Default is 30 days", value=30)

        colA, colB, colC = st.columns(3)

        p = colA.number_input(
            "p (AR order)", 0, 5, 1,
            help="Autoregressive order: Number of previous timepoints used to predict current value. Typical: 1-3."
        )
        d = colA.number_input(
            "d (Difference order)", 0, 2, 1,
            help="Number of times the series is differenced to make it stationary. Usually 1 for energy data."
        )
        q = colA.number_input(
            "q (MA order)", 0, 5, 1,
            help="Moving average order: How many past forecast errors are included. Typical: 0-2."
        )

        P = colB.number_input(
            "P (Seasonal AR)", 0, 5, 1,
            help="Seasonal autoregressive order: Like 'p' but for seasonal component. 1-2 for daily/weekly seasonality."
        )
        D = colB.number_input(
            "D (Seasonal Difference)", 0, 1, 1,
            help="Seasonal differencing: Remove repeating seasonal patterns. Usually 1 for hourly/daily data with weekly seasonality."
        )
        Q = colB.number_input(
            "Q (Seasonal MA)", 0, 5, 1,
            help="Seasonal moving average order: Like 'q' but for seasonal residuals. Typical: 0-2."
        )

        seasonal_period = colC.number_input(
            "Seasonal period", 1, 168, 24,
            help="Length of the repeating seasonal cycle. 24 for daily seasonality, 168 for weekly."
        )


        if st.button("Run SARIMAX Forecast"):
            with st.spinner("Training SARIMAX model..."):

                # Work with a COPY of the dataframe
                df_forecast = st.session_state.df.copy()
                
                # Set starttime as index
                df_forecast['starttime'] = pd.to_datetime(df_forecast['starttime'])
                df_forecast = df_forecast.set_index('starttime')

                # Fit model on training data
                model = sm.tsa.statespace.SARIMAX(
                    df_forecast["quantitykwh"],
                    order=(p, d, q),
                    seasonal_order=(P, D, Q, seasonal_period),
                    trend="c",
                    enforce_stationarity=False,
                    enforce_invertibility=False
                )
                results = model.fit(disp=False)

                # Full model for forecasting 
                model_full = sm.tsa.statespace.SARIMAX(
                    df_forecast["quantitykwh"],
                    order=(p, d, q),
                    seasonal_order=(P, D, Q, seasonal_period),
                    trend="c",
                    enforce_stationarity=False,
                    enforce_invertibility=False
                )
                results_full = model_full.filter(results.params)

                # Dynamic forecast starting from last training timestamp
                last_train_time = df_forecast.index[-1]
                forecast_obj = results_full.get_prediction(
                    start=last_train_time,
                    end=last_train_time + pd.Timedelta(days=forecast_days),
                    dynamic=True
                )

                # Predicted value with confidence interval
                forecast_mean = forecast_obj.predicted_mean
                forecast_ci = forecast_obj.conf_int()

                st.subheader("Forecast Results")
                fig = go.Figure()

                # Plot observed data
                fig.add_trace(go.Scatter(
                    x=df_forecast.index,
                    y=df_forecast["quantitykwh"],
                    mode="lines",
                    name="Observed"
                ))

                # Plot forecast
                fig.add_trace(go.Scatter(
                    x=forecast_mean.index[1:],
                    y=forecast_mean.values[1:],
                    mode="lines",
                    name="Forecast",
                    line=dict(dash="dash", color="red")
                ))

                # Plot confidence interval
                fig.add_trace(go.Scatter(
                    x=forecast_ci.index[1:],
                    y=forecast_ci.iloc[1:, 0],
                    fill=None,
                    mode="lines",
                    line=dict(width=0),
                    showlegend=False
                ))

                fig.add_trace(go.Scatter(
                    x=forecast_ci.index[1:],
                    y=forecast_ci.iloc[1:, 1],
                    fill="tonexty",
                    mode="lines",
                    line=dict(width=0),
                    name="Confidence Interval",
                    fillcolor="rgba(255, 0, 0, 0.2)"
                ))

                fig.update_layout(
                    title=f"SARIMAX Forecast for ENERGY {st.session_state.database}, in pricearea {st.session_state.selected_pricearea}, type {st.session_state.group_selected}",
                    xaxis_title="Time",
                    yaxis_title="kWh",
                    height=600,
                    xaxis=dict(type="date")  # Ensure x-axis is treated as dates
                )

                st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("Please query the database before running SARIMAX")    

def sarimax_page():
    sarimax()