from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv

load_dotenv()

USR,PWD = os.getenv("DB_USER"), os.getenv("DB_PWD")

uri = f"mongodb+srv://{USR}:{PWD}@ind320.nxw58bh.mongodb.net/?retryWrites=true&w=majority&appName=IND320"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)