import streamlit as st
import pandas as pd
from pymongo import MongoClient

@st.cache_data
def load_data(file):
    return pd.read_csv(file)

@st.cache_data
def load_data_from_mongodb():
    """Load all data from MongoDB and return as pandas DataFrame"""
    # Connecting to MongoDB
    uri = st.secrets["mongo"]["uri"]
    db_name = st.secrets["mongo"]["database"]
    client = MongoClient(uri)
    db = client[db_name]
    collection = db["production_NO1"]

    # Fetch all documents
    #documents = list(collection.find())
    documents = list(collection.find())
    
    # Close the connection
    client.close()
    
    # Convert to DataFrame
    df = pd.DataFrame(documents)
    
    # Optional: Remove the MongoDB _id field if you don't need it
    if '_id' in df.columns:
        df = df.drop('_id', axis=1)
    
    return df