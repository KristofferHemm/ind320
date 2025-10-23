import streamlit as st
import pandas as pd
from pymongo import MongoClient
from second import second_page
from third import third_page
from fourth import fourth_page
from fifth import fifth_page

# Connecting to MongoDB
uri = st.secrets["mongo"]["uri"]
db_name = st.secrets["mongo"]["database"]
client = MongoClient(uri)
db = client[db_name]

# Read data from MongoDB
users_collection = db["production_NO1"]
st.write(list(users_collection.find()))

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

# Sidebar navigation
page = st.sidebar.selectbox("Navigate", ["Home", "Second", "Third", "Fourth", "Fifth"])

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