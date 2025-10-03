import streamlit as st
import pandas as pd

@st.cache_data
def load_data(file):
    return pd.read_csv(file)
