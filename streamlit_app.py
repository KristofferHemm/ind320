import streamlit as st
from second import second_page

# Define pages as functions
def home():
    st.title("Home Page")
    st.write("Use the navigation bar to the left")

def second():
    st.title("Second Page")
    second_page()

def third():
    st.title("Third Page")
    st.write("This is the third page")

# Sidebar navigation
page = st.sidebar.selectbox("Navigate", ["Home", "Second", "Third"])

# Display the selected page
if page == "Home":
    home()
elif page == "Second":
    second()
elif page == "Third":
    third()