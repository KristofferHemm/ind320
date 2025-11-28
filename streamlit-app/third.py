import streamlit as st
import altair as alt
import pandas as pd
from load_data import load_data, load_data_from_meteo

def month_slicer(df):

    """ 
    Add month slicer
    Input: df
    Output: tuple
    """

    df['time'] = pd.to_datetime(df['date'])
    df['month'] = df['time'].dt.to_period('M').astype(str)

    # Create month slicer
    month_options = sorted(df['month'].unique())
    selected_months = st.select_slider(
        'Select the subset of months to view',
        options=month_options,
        value=(month_options[0], month_options[0]) 
    )

    return selected_months


def column_slicer(df):

    """
    Make column slicer
    Input: df
    Output: list, string
    """

    column_options = ['All columns'] + [col for col in df.columns if col not in ['date', 'time', 'month']]
    selected_column = st.selectbox('Select which column to view', column_options)
    
    return column_options, selected_column


def month_subset(df, selected_months):

    """
    Make subset of selected months
    Input: df
    Outpu: df
    """

    start_month, end_month = selected_months
    mask = (df['month'] >= start_month) & (df['month'] <= end_month)
    df = df[mask]

    return df


def plotter(selected_column, column_options, df):

    """
    Plot the selceted months and columns
    """

    if selected_column == "All columns":
        # Melt the DataFrame for Altair
        melted = df.melt(id_vars='time', value_vars=column_options[1:], var_name='Series', value_name='Value')

        chart = alt.Chart(melted).mark_line().encode(
            x=alt.X('time:T', title='Time'),
            y=alt.Y('Value:Q', title='Value'),
            color='Series:N'
        ).properties(
            title='Time Series Plot of All Columns',
            width=800,
            height=400
        ).interactive()
    else:
        chart = alt.Chart(df).mark_line().encode(
            x=alt.X('time:T', title='Time'),
            y=alt.Y(f'{selected_column}:Q', title=selected_column),
        ).properties(
            title=f'Time Series Plot of {selected_column}',
            width=800,
            height=400
        ).interactive()

    # Display the chart
    st.altair_chart(chart, use_container_width=True)


def third_page():

    """
    Create page containing line plot of the imported data.
    Controls: Drop down for selecting column and slider for selecting month range and
    """
    
    # Generate list of cities for user selection and set it as the session state
    if 'selected_city' not in st.session_state:
        st.session_state.selected_city = "Bergen"

    cities = ["Bergen", "Oslo", "Kristiansand", "Trondheim", "Tromsø"]
    st.session_state.selected_city = st.selectbox(
    "Select a city:",
    options=cities,
    index=cities.index(st.session_state.selected_city)
    )

    # Generate list of years for user selection and set it as the session state
    if 'selected_year' not in st.session_state:
        st.session_state.selected_year = 2021

    years = list(range(2021, 2025, 1))
    st.session_state.selected_year = st.selectbox(
        "Select a year:",
        options=years,
        index=years.index(st.session_state.selected_year)
    )

    # Load data
    df = load_data_from_meteo(st.session_state.selected_year, st.session_state.selected_city)

    # Create slicers and filter data
    selected_months = month_slicer(df)    
    column_options, selected_column = column_slicer(df)
    filtered_df = month_subset(df, selected_months)

    # Plotting
    st.subheader("Time Series Plot")
    plotter(selected_column, column_options, filtered_df)
    