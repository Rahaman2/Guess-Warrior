import pymongo
from dotenv import load_dotenv
import os








load_dotenv()

try:
    mongodb_uri = os.getenv("MONGO_URI")
    client = pymongo.MongoClient(mongodb_uri)
    print("Succesfully connected to database")

except:
    print("Something went wrong whilest establishing the connection")


    

db = client.get_database("family_feud")
users = db.get_collection("users")


def save_user(user:dict, users):
    saved_user = users.insert_one(user)
    return saved_user


def delete_user(user, users):
    users.delete_one(user)


def update_user(user, users):
    users.update_one(user)

    




