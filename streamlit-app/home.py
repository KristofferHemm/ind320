import streamlit as st

def home_page():
    st.title("Weather and energy dashboard")
    st.subheader("Welcome to the weather and energy dashboard!")
    st.write("To the left you will find a menu to navigate the dashboard.")
    st.write("The first two pages display weather data.")
    st.write("The next four pages display energy data, including an energy forecast.")
    st.write("The last two pages display calculation of snowdrift and correlation between energy and weather data.")