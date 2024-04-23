import pymongo
from dotenv import load_dotenv
import os

myclient = pymongo.MongoClient


load_dotenv()

try:
    mongodb_uri = os.getenv("MONGO_URI")
    print("Succesfully connected to database")
except:
    print("Something went wrong whilest establishing the connection")


    
    


client = pymongo.MongoClient(mongodb_uri)

db = client.get_database("family_feud")

# collection_names = db.get_collection("users")
users = db.get_collection("users")

# all_users = users.find({"name": "Ned Stark"})

# for user in all_users:
#     print(user)

# print("Collections in the user Database")
# for collection_name in collection_names:
#     print(collection_name)

