import pandas as pd
import streamlit as st
from datetime import datetime
from load_data import load_data, load_data_from_meteo

def second_page():
    
    """
    Create page containing row-wise line chart of the first month of data
    """

    
    st.write("Please select the city and year you want to explore below.")
    st.write("Default selection is for Bergen in 2021.")


    # Generate list of cities for user selection
    cities = [ "Bergen", "Oslo", "Kristiansand", "Trondheim", "Tromsø"]
    selected_city = st.selectbox(
    "Select a city:",
    options=cities
    )

    # Generate list of years for user selection
    years = list(range(2021, 2025, 1))
    selected_year = st.selectbox(
    "Select a year:",
    options=years
    )

    # Load data
    df = load_data_from_meteo(selected_year, selected_city)

    # Choose the first month of the data
    df['date'] = pd.to_datetime(df["date"])
    df = df.set_index('date')
    first_month = df[df.index.month == df.index[0].month]

    chart_df = pd.DataFrame({
        'Series': first_month.columns,
        'Trend': [first_month[col].tolist() for col in first_month.columns]
    })

    # Plot the first month of data
    st.write('Row-wise line chart of the first month of data')
    st.dataframe(
        chart_df,
        column_config={
            "Trend": st.column_config.LineChartColumn(
                "First Month Trend",
                y_min=first_month.min().min(),
                y_max=first_month.max().max(),
            )
        },
        hide_index=True
    )