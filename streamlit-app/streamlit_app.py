import streamlit as st
import pandas as pd
from home import home_page
from weather_data import weather_data_page
from fourth import fourth_page
from newA import newA_page
from newB import newB_page
from map import map_page
from snowdrift import snowdrift_page
from sarimax import sarimax_page
from sliding_window_correlation import sliding_window_page

# Define pages as functions
def home():
    home_page()

def weather_data():
    weather_data_page()

def fourth():
    fourth_page()

def newA():
    newA_page()

def newB():
    newB_page()

def map():
    map_page()

def snowdrift():
    snowdrift_page()

def sarimax():
    sarimax_page()

def sliding_window():
    sliding_window_page()

# Sidebar navigation
page = st.sidebar.selectbox("Navigate", ["Home", "Weather data", "Weather data outliers", "Energy production", "Energy plots", "SARIMAX", "Energy map", "Snowdrift", "Sliding window"])

# Display the selected page
if page == "Home":
    home()
elif page == "Weather data":
    weather_data()
elif page == "Energy production":
    fourth()
elif page == "Energy plots":
    newA()
elif page == "Weather data outliers":
    newB()
elif page == "Energy map":
    map()
elif page == "Snowdrift":
    snowdrift()
elif page == "SARIMAX":
    sarimax()
elif page == "Sliding window":
    sliding_window()