import pandas as pd
import streamlit as st

def second_page():
    df = pd.read_csv('open-meteo-subset.csv')

    df['time'] = pd.to_datetime(df['time'])

    df = df.set_index('time')
    
    first_month = df[df.index.month == df.index[0].month]

    chart_df = pd.DataFrame({
        'Series': first_month.columns,
        'Trend': [first_month[col].tolist() for col in first_month.columns]
    })

    st.write("Row-wise line chart of the first month of data")
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