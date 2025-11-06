import streamlit as st
import pandas as pd
from pymongo import MongoClient
import openmeteo_requests
from retry_requests import retry
import requests_cache

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

@st.cache_data
def load_data_from_meteo(year=2021):
    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)
    cities = {
    'Oslo':
        {"price_area_code": "NO1",
         "longitude": 10.7461,
         "latitude": 59.9127
        },
    'Kristiansand':
        {"price_area_code": "NO2",
         "longitude": 7.9956,
         "latitude": 58.1467
        },
    'Trondheim':
        {"price_area_code": "NO3",
         "longitude": 10.3951,
         "latitude": 63.4305        
        },
    'Tromsø':
        {"price_area_code": "NO4",
         "longitude": 18.9551,
         "latitude": 69.6489        
        },
    'Bergen':
        {"price_area_code": "NO5",
         "longitude": 5.3242,
         "latitude": 60.393        
        }
    }
    df_hourly = pd.DataFrame(cities)
    def create_dates(year):
        start = f'{year}-01-01'
        end = f'{year}-12-31'
        return start, end
    
    def fetch_data(longitude, latitude, year):
        start, end = create_dates(year)
        params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start,
        "end_date": end,
        "hourly": ["temperature_2m", "precipitation", "wind_speed_10m", "wind_gusts_10m", "wind_direction_10m"],
        }
        url = "https://historical-forecast-api.open-meteo.com/v1/forecast"
        responses = openmeteo.weather_api(url, params=params)
        return responses
    
    fetch_data(df_hourly.Bergen.longitude, df_hourly.Bergen.latitude, year)