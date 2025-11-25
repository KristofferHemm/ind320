import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy.fft import dct, idct
from sklearn.neighbors import LocalOutlierFactor
from load_data import load_data_from_meteo

def plot_summary_satv(df, cutoff=100, k=3.0):
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

    df = df.copy()

    # High pass filtering
    temp_dct_ortho = dct(df['temperature_2m'], norm='ortho')
    temp_dct_ortho[:cutoff] = 0
    df['temp_highpass'] = idct(temp_dct_ortho, norm='ortho')
    df['seasonal'] = df['temperature_2m'] - df['temp_highpass']

    # Seasonally adjusted temperature variations
    median_satv = np.median(df['temp_highpass'])
    mad_satv = np.median(np.abs(df['temp_highpass'] - median_satv))
    upper_satv = median_satv + k * mad_satv
    lower_satv = median_satv - k * mad_satv

    df['ucl'] = df['seasonal'] + upper_satv
    df['lcl'] = df['seasonal'] + lower_satv

    # Add outliers to df
    df['is_outlier'] = (df['temp_highpass'] > upper_satv) | (df['temp_highpass'] < lower_satv)

    # Plotting
    fig = go.Figure()
    
    # Original temperature_2m trace
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['temperature_2m'],
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
        x=df['date'],
        y=df['ucl'],
        mode='lines',
        name='UCL (Upper Control Limit)',
        line=dict(color='green', dash='dash')
    ))
    
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['lcl'],
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

    # Create summary
    total_points = len(df)
    n_outliers = df['is_outlier'].sum()
    outlier_pct = 100 * n_outliers / total_points

    normal_mean = df.loc[~df['is_outlier'], 'temperature_2m'].mean() if n_outliers < total_points else np.nan
    outlier_mean = df.loc[df['is_outlier'], 'temperature_2m'].mean() if n_outliers > 0 else np.nan
    outlier_max = df.loc[df['is_outlier'], 'temperature_2m'].max() if n_outliers > 0 else np.nan
    outlier_min = df.loc[df['is_outlier'], 'temperature_2m'].min() if n_outliers > 0 else np.nan
    first_outlier = df.loc[df['is_outlier'], 'date'].min() if n_outliers > 0 else np.nan
    last_outlier = df.loc[df['is_outlier'], 'date'].max() if n_outliers > 0 else np.nan

    summary = pd.DataFrame([{
        'Total Points': total_points,
        'Detected Outliers': n_outliers,
        'Outlier %': round(outlier_pct, 3),
        'Normal Mean': round(normal_mean, 3),
        'Outlier Mean': round(outlier_mean, 3),
        'Outlier Max': round(outlier_max, 3),
        'Outlier Min': round(outlier_min, 3),
        'First Outlier': first_outlier,
        'Last Outlier': last_outlier
    }])

    return fig, summary

def plot_summary_lof(df, outlier_fraction=0.01):
    """
    Input:
    df : pd.DataFrame
    outlier_fraction : float

    Returns
    -------
    fig : plotly.graph_objects.Figure
    summary : pd.DataFrame
    """
    
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])

    # Feature for anomaly detection
    X = df[["precipitation"]].values

    # Local Outlier Factor
    lof = LocalOutlierFactor(n_neighbors=20, contamination=outlier_fraction)
    labels = lof.fit_predict(X)
    df["anomaly"] = labels == -1
    anomalies = df[df["anomaly"]]

    # Plotting
    fig = go.Figure()

    # Normal points (blue line)
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["precipitation"],
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

    # Create summary
    summary_data = {
            "Total Points": [len(df)],
            "Detected Anomalies": [len(anomalies)],
            "Anomaly %": [len(anomalies) / len(df) * 100],
            "Normal Mean": [df["precipitation"].mean()],
            "Anomaly Mean": [anomalies["precipitation"].mean()],
            "Anomaly Max": [anomalies["precipitation"].max()],
            "Anomaly Min": [anomalies["precipitation"].min()],
            "First Anomaly": [anomalies["date"].min()],
            "Last Anomaly": [anomalies["date"].max()]
        }
    summary = pd.DataFrame(summary_data)

    return fig, summary
