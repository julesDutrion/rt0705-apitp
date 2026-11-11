
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from urllib.parse import quote_plus

load_dotenv()

username = quote_plus(os.getenv("MONGO_USERNAME"))
password = quote_plus(os.getenv("MONGO_PASSWORD"))
host = os.getenv("MONGO_HOST")
port = os.getenv("MONGO_PORT")
database = os.getenv("MONGO_DATABASE")
authSource = os.getenv("MONGO_AUTH_SOURCE")

uri = (
    f"mongodb://{username}:{password}@{host}:{port}/"
    f"{database}?authSource={authSource}"
)

client = MongoClient(uri)
db = client[database]
