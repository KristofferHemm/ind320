import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy.fft import dct, idct
from sklearn.neighbors import LocalOutlierFactor
from load_data import load_data_from_meteo

def plot_summary_temperature(df_hourly, cutoff=100, k=3.0):
    """
    Input:
    df : pd.DataFrame
    cutoff : int
    k : float

    Returns
    -------
    fig : plotly.graph_objects.Figure
    summary : pd.DataFrame
    """

    df = df_hourly.copy()
    
    # High pass filtering
    temp_dct_ortho = dct(df.temperature_2m, norm='ortho')

    temp_dct_ortho[:cutoff] = 0
    df['temp_highpass'] = idct(temp_dct_ortho, norm='ortho')

    # Seasonally adjusted temperature variations
    median_satv = np.median(df['temp_highpass'])
    mad_satv = np.median(np.abs(df['temp_highpass'] - median_satv))
    
    k = 3.0  # typical SPC multiplier
    ucl = median_satv + k * mad_satv
    lcl = median_satv - k * mad_satv
    
    df['is_outlier'] = (df['temp_highpass'] > ucl) | (df['temp_highpass'] < lcl)

    # Plotting
    fig = go.Figure()
    
    # Original temperature_2m trace
    fig.add_trace(go.Scatter(
        x=df_hourly['date'],
        y=df_hourly['temperature_2m'],
        mode='lines',
        name='Original temperature'
    ))

    # Outliers
    fig.add_trace(go.Scatter(
        x=df.loc[df['is_outlier'], 'date'],
        y=df.loc[df['is_outlier'], 'temperature_2m'],
        mode='markers',
        name='Outliers',
        marker=dict(color='red', size=4, symbol='circle'),
    ))

    # SPC boundaries (horizontal lines)
    fig.add_trace(go.Scatter(
        x=[df['date'].min(), df['date'].max()],
        y=[ucl, ucl],
        mode='lines',
        name='UCL (Upper Control Limit)',
        line=dict(color='green', dash='dash')
    ))
    
    fig.add_trace(go.Scatter(
        x=[df['date'].min(), df['date'].max()],
        y=[lcl, lcl],
        mode='lines',
        name='LCL (Lower Control Limit)',
        line=dict(color='green', dash='dash')
    ))
    
    # Layout
    fig.update_layout(
        title='Temperature with SPC Outlier Detection (Seasonally Adjusted via DCT)',
        xaxis_title='Date',
        yaxis_title='Temperature (°C)',
        template='plotly_white',
        legend=dict(yanchor='top', y=0.98, xanchor='left', x=0.01),
        height=600
    )
    
    
    summary = df.loc[df['is_outlier'], ['date', 'temperature_2m', 'temp_highpass']].copy()
    summary['deviation'] = df.loc[df['is_outlier'], 'temp_highpass'] - median_satv
    summary['limit'] = np.where(summary['temp_highpass'] > ucl, 'above UCL', 'below LCL')

    return fig, summary

def plot_precip_anomalies(df, outlier_fraction=0.01):
    
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])

    # Feature for anomaly detection
    X = df[["precipitation"]].values

    # Local Outlier Factor
    lof = LocalOutlierFactor(n_neighbors=20, contamination=outlier_fraction)
    labels = lof.fit_predict(X)
    df["anomaly"] = labels == -1
    
    anomalies = df[df["anomaly"]]
    normal = df[~df["anomaly"]]

    # Create Plotly figure 
    fig = go.Figure()

    # Normal points (blue line)
    fig.add_trace(go.Scatter(
        x=normal["date"], y=normal["precipitation"],
        mode="lines", name="Normal", line=dict(color="blue")
    ))

    # Anomalies (red markers)
    fig.add_trace(go.Scatter(
        x=anomalies["date"], y=anomalies["precipitation"],
        mode="markers", name="Anomaly",
        marker=dict(color="red", size=4, symbol="circle")
    ))

    fig.update_layout(
        title=f"Precipitation with Anomalies (LOF, {outlier_fraction*100:.1f}% expected outliers)",
        xaxis_title="Date-Time",
        yaxis_title="Precipitation",
        template="plotly_white",
        legend_title="Type"
    )

    summary_data = {
            "Total Points": [len(df)],
            "Detected Anomalies": [len(anomalies)],
            "Anomaly %": [len(anomalies) / len(df) * 100],
            "Normal Mean": [normal["precipitation"].mean()],
            "Anomaly Mean": [anomalies["precipitation"].mean()],
            "Anomaly Max": [anomalies["precipitation"].max()],
            "Anomaly Min": [anomalies["precipitation"].min()],
            "First Anomaly": [anomalies["date"].min()],
            "Last Anomaly": [anomalies["date"].max()]
        }
    summary = pd.DataFrame(summary_data)

    return fig, summary



def newB_page():
    
    st.write("Please choose which plot you want to see below.")

    tab1, tab2 = st.tabs(["SPC analysis", "LOF analysis"])

    if 'selected_year' in st.session_state:
        selected_year = st.session_state.selected_year
        
    else:
        st.warning("Please select a year on the second page first")

    if 'selected_city' in st.session_state:
        selected_city = st.session_state.selected_city
    else:
        st.warning("Please select a city on the second page first")

    # Load data
    df = load_data_from_meteo(st.session_state.selected_year, st.session_state.selected_city)
    
    # Content for Tab 1
    with tab1:
        st.header("SPC analysis")
        st.write(f"Using data from year: {selected_year}")
        st.write(f"Using data from city: {selected_city}")
        fig, summary = plot_summary_temperature(df)
        st.plotly_chart(fig)
        st.write(summary.head())

    # Content for Tab 2
    with tab2:
        st.header("LOF analysis")
        st.write(f"Using data from year: {selected_year}")
        st.write(f"Using data from city: {selected_city}")
        fig, summary = plot_precip_anomalies(df)
        st.plotly_chart(fig)
        st.write(summary)