import streamlit as st
import pandas as pd
from home import home_page
from weather_data import weather_data_page
from energy_production import energy_production_page
from newA import newA_page
from weather_data_outliers import weather_data_outliers_page
from map import map_page
from snowdrift import snowdrift_page
from sarimax import sarimax_page
from sliding_window_correlation import sliding_window_page

# Define pages as functions
def home():
    home_page()

def weather_data():
    weather_data_page()

def energy_production():
    energy_production_page()

def newA():
    newA_page()

def weather_data_ouliers():
    weather_data_outliers_page()

def map():
    map_page()

def snowdrift():
    snowdrift_page()

def sarimax():
    sarimax_page()

def sliding_window():
    sliding_window_page()

# Sidebar navigation
page = st.sidebar.selectbox("Navigate", ["Home", "Weather data", "Weather data outliers", "Energy production", "Energy plots", "Energy forecasting", "Energy map", "Snowdrift", "Sliding window"])

# Display the selected page
if page == "Home":
    home()
elif page == "Weather data":
    weather_data()
elif page == "Energy production":
    energy_production()
elif page == "Energy plots":
    newA()
elif page == "Weather data outliers":
    weather_data_ouliers()
elif page == "Energy map":
    map()
elif page == "Snowdrift":
    snowdrift()
elif page == "Energy forecasting":
    sarimax()
elif page == "Sliding window":
    sliding_window()