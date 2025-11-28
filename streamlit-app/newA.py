import pandas as pd
import streamlit as st
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import numpy as np
from statsmodels.tsa.seasonal import STL
from statsmodels.nonparametric.smoothers_lowess import lowess
from scipy.signal import stft
from load_data import load_data_from_mongodb_no_arguments

def _make_odd(x):
    """Return an odd integer >= 3 from x (int or None)."""
    if x is None:
        return None
    x = int(x)
    if x < 3:
        return 3
    return x if x % 2 == 1 else x + 1

def loess_decompose_and_plot(
    df,
    pricearea=None,
    productiongroup=None,
    period_length=24,
    seasonal_smoother=None,
    trend_smoother=None,
    robust=False,
    resample_rule=None,
    lowess_frac=0.1,
    ):

    """
    Seasonal trend decomposition (which uses local regression / loess internally),
    and plot original series, trend, seasonal and residual components.

    Parameters:
    df : pandas.DataFrame
    pricearea=None,
    productiongroup=None,
    period_length=24,
    seasonal_smoother=None,
    trend_smoother=None,
    robust=False,
    resample_rule=None,
    lowess_frac=0.1
    
    Returns:
    fig : plotly.graph_objects.Figure
    """

    df = df.copy()
    df['starttime'] = pd.to_datetime(df['starttime'])
    df = df.sort_values('starttime')
    series = df.groupby('starttime')['quantitykwh'].sum()
    series = series.sort_index()
    n = len(series)

    # Prepare STL parameters
    seasonal = _make_odd(seasonal_smoother if seasonal_smoother is not None else period_length)
    trend = _make_odd(trend_smoother if trend_smoother is not None else max(7, int(period_length * 1.5)))
    
    # Ensure seasonal < n and trend < n
    seasonal = seasonal if (seasonal is None or seasonal < n) else _make_odd(max(3, n - 2))
    trend = trend if (trend is None or trend < n) else _make_odd(max(3, n - 2))

    stl = STL(series, period=period_length, seasonal=seasonal, trend=trend, robust=robust)
    res = stl.fit()
    
    lowess_sm = lowess(series.values, np.arange(n), frac=lowess_frac, return_sorted=False)
    
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=('Original series and LOWESS overlay', 'Trend', 'Seasonal', 'Residual')
    )
    
    # Original series
    fig.add_trace(
        go.Scatter(x=series.index, y=series.values, mode='lines', name='Original'),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=series.index, y=lowess_sm, mode='lines', name='LOWESS', 
                   line=dict(dash='dash')),
        row=1, col=1
    )
    
    # Trend
    fig.add_trace(
        go.Scatter(x=series.index, y=res.trend, mode='lines', name='Trend'),
        row=2, col=1
    )
    
    # Seasonal
    fig.add_trace(
        go.Scatter(x=series.index, y=res.seasonal, mode='lines', name='Seasonal'),
        row=3, col=1
    )
    
    # Residual
    fig.add_trace(
        go.Scatter(x=series.index, y=res.resid, mode='lines', name='Residual'),
        row=4, col=1
    )
    
    # Update axes labels
    fig.update_yaxes(title_text="quantitykwh", row=1, col=1)
    fig.update_yaxes(title_text="Trend", row=2, col=1)
    fig.update_yaxes(title_text="Seasonal", row=3, col=1)
    fig.update_yaxes(title_text="Residual", row=4, col=1)
    fig.update_xaxes(title_text="time", row=4, col=1)
    
    # Update layout
    fig.update_layout(
        height=800,
        showlegend=True,
        hovermode='x unified'
    )
    
    return fig


def plot_spectrogram_stft(df, pricearea='NO1', productiongroup='hydro',
                          resample_freq='15min', window_length='2H', overlap=0.5):
    """
    Plot a spectrogram of energy production using scipy.signal.stft.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with columns ['starttime', 'pricearea', 'productiongroup', 'quantitykwh'].
    pricearea : str, default 'NO1'
        Filter for this price area.
    productiongroup : str, default 'Hydro'
        Filter for this production group.
    resample_freq : str, default '15min'
        Frequency to resample the data to uniform spacing.
    window_length : str, default '2H'
        Window length for STFT.
    overlap : float, default 0.5
        Overlap ratio between consecutive windows (0 < overlap < 1).

    Returns
    -------
    fig : plotly.graph_objects.Figure

    """
    
    # Filter data
    dff = df[(df['pricearea'] == pricearea) & (df['productiongroup'] == productiongroup)].copy()
    if dff.empty:
        raise ValueError("No data for the given filters.")

    # Ensure datetime and sort
    dff['starttime'] = pd.to_datetime(dff['starttime'])
    dff.sort_values('starttime', inplace=True)
    dff.set_index('starttime', inplace=True)

    # Resample to a regular time step
    dff = dff['quantitykwh'].resample(resample_freq).mean().interpolate()
    signal = dff.values

    # Compute parameters for STFT
    fs = 1 / pd.to_timedelta(resample_freq).total_seconds()  # Sampling frequency [Hz]
    nperseg = int(pd.to_timedelta(window_length).total_seconds() / pd.to_timedelta(resample_freq).total_seconds())
    noverlap = int(nperseg * overlap)

    # Compute STFT
    f, t, Zxx = stft(signal, fs=fs, nperseg=nperseg, noverlap=noverlap)

    # Create Plotly heatmap
    fig = go.Figure(data=go.Heatmap(
        x=t,
        y=f,
        z=np.abs(Zxx),
        colorscale='Viridis',
        colorbar=dict(title='|Amplitude|')
    ))

    fig.update_layout(
        title=f"Spectrogram (STFT) for {productiongroup} in {pricearea}",
        xaxis_title='Time [s]',
        yaxis_title='Frequency [Hz]',
        width=1000,
        height=400
    )

    return fig


def newA_page():

    # Initialize df
    df = None
    
    st.subheader("Seasonal-Trend decomposition and Spectrogram of energy data")
    st.write("Please click the Query Data button to load data into the plots.")
    st.write("Please choose which plot you want to see below.")

    tab1, tab2 = st.tabs(["STL analysis", "Spectrogram"])

    # Load data
    if st.button("Query Data"):
        with st.spinner("Querying database..."):
            df = load_data_from_mongodb_no_arguments()

    if df is not None:
        # Content for Tab 1
        with tab1:
            st.header("STL analysis")
            fig = loess_decompose_and_plot(df)
            st.plotly_chart(fig)

        # Content for Tab 2
        with tab2:
            st.header("Spectrogram")
            fig = plot_spectrogram_stft(df)
            st.plotly_chart(fig)
    else:
        st.write("Please query the data to see the plots")