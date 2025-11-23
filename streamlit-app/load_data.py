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
def load_data_from_meteo(year, city):
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

    selected_city = cities[city]

    start = f'{year}-01-01'
    end = f'{year}-12-31'

    params = {
    "latitude": selected_city['latitude'], 
    "longitude": selected_city['longitude'],
    "start_date": start,
    "end_date": end,
    "hourly": ["temperature_2m", "precipitation", "wind_speed_10m", "wind_gusts_10m", "wind_direction_10m"],
    }
    url = "https://historical-forecast-api.open-meteo.com/v1/forecast"
    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]
    # Process hourly data. The order of variables needs to be the same as requested.
    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_precipitation = hourly.Variables(1).ValuesAsNumpy()
    hourly_wind_speed_10m = hourly.Variables(2).ValuesAsNumpy()
    hourly_wind_gusts_10m = hourly.Variables(3).ValuesAsNumpy()
    hourly_wind_direction_10m = hourly.Variables(4).ValuesAsNumpy()

    hourly_data = {"date": pd.date_range(
        start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
        end =  pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
        freq = pd.Timedelta(seconds = hourly.Interval()),
        inclusive = "left"
    )}

    hourly_data["temperature_2m"] = hourly_temperature_2m
    hourly_data["precipitation"] = hourly_precipitation
    hourly_data["wind_speed_10m"] = hourly_wind_speed_10m
    hourly_data["wind_gusts_10m"] = hourly_wind_gusts_10m
    hourly_data["wind_direction_10m"] = hourly_wind_direction_10m

    df = pd.DataFrame(data = hourly_data)

    # Need to convert to float64 for the data to work in Streamlit
    for col in df.select_dtypes(include=["float32", "float16"]).columns:
        df[col] = df[col].astype("float64")

    return df
