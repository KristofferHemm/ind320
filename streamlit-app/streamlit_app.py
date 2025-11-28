import streamlit as st
import pandas as pd
from home import home_page
from third import third_page
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

def third():
    third_page()

def fourth():
    st.title("Fourth Page")
    fourth_page()

def newA():
    st.title("New A")
    newA_page()

def newB():
    st.title("New B")
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
page = st.sidebar.selectbox("Navigate", ["Home", "Weather data", "Weather data outliers", "Energy map", "Fourth", "newA", "Sarimax", "Snowdrift", "Sliding window"])

# Display the selected page
if page == "Home":
    home()
elif page == "Weather data":
    third()
elif page == "Fourth":
    fourth()
elif page == "newA":
    newA()
elif page == "Weather data outliers":
    newB()
elif page == "Energy map":
    map()
elif page == "Snowdrift":
    snowdrift()
elif page == "Sarimax":
    sarimax()
elif page == "Sliding window":
    sliding_window()