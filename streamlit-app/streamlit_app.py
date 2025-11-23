import streamlit as st
import pandas as pd
from second import second_page
from third import third_page
from fourth import fourth_page
from fifth import fifth_page
from newA import newA_page
from newB import newB_page

# Define pages as functions
def home():
    st.title("Home Page")
    st.write("Use the navigation bar to the left")

def second():
    st.title("Second Page")
    second_page()

def third():
    st.title("Third Page")
    third_page()

def fourth():
    st.title("Fourth Page")
    fourth_page()

def fifth():
    st.title("Fifth Page")
    fifth_page()

def newA():
    st.title("New A")
    newA_page()

def newB():
    st.title("New B")
    newB_page()

# Sidebar navigation
page = st.sidebar.selectbox("Navigate", ["Home", "Fourth", "newA", "Second", "Third", "newB", "Fifth"])

# Display the selected page
if page == "Home":
    home()
elif page == "Second":
    second()
elif page == "Third":
    third()
elif page == "Fourth":
    fourth()
elif page == "Fifth":
    fifth()
elif page == "newA":
    newA()
elif page == "newB":
    newB()