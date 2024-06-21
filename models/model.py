from pymongo import MongoClient
from dotenv import load_dotenv
import os
import bcrypt

load_dotenv()

mongodb_uri = os.getenv("MONGO_URI")
# client = MongoClient('mongodb://localhost:27017/')
client = MongoClient(mongodb_uri)
db = client['family_feud_game']
users_collection = db['users']
scores_collection = db['scores']



def hashPassword( password:str ):
    bytes = password.encode("utf-8")
    salt = bcrypt.gensalt( 10 )
    hash = bcrypt.hashpw(bytes, salt)
    return hash

def add_User(username, password, email) -> bool:
    user_info = {
        'username': username,
        'email': email,
        'password': hashPassword(password)
    }

    existing_user = users_collection.find_one({'username': username})

    if existing_user:
        return False
    else:
        inserted_user = users_collection.insert_one(user_info)
        
        create_score( inserted_user.inserted_id , 0, 0)
        return True


def create_score(user_id, total_points, games_played):
    score_info = {
    'user_id': user_id,
    'joined': '2024-06-20',
    'score': total_points,
    'games_played': games_played
    }
    scores_collection.insert_one(score_info)
    
# add_User("rahaman", "12345", "rahaman@yahoo.com")
# def update_score(user_id, newScore, games_played):
#     score_info = {
#     'user_id': user_id,
#     'joined': '2024-06-20',
#     'score': newScore,
#     'games_played': games_played
#     }
#     scores_collection.update_one({user_id})


# # Insert a sample user
# user_data = {
#     'username': 'player1',
#     'email': 'player1@example.com',
#     'password': 'password123'  # Note: In production, passwords should be hashed
# }
# inserted_user = users_collection.insert_one(user_data)
# user_id = inserted_user.inserted_id  # Retrieve the inserted user's ID

# # Insert a sample score linked to the user
# score_data = {
#     'user_id': user_id,
#     'game_date': '2024-06-20',
#     'score': 1000
# }
# scores_collection.insert_one(score_data)


# # Find a user by username
# user = users_collection.find_one({'username': 'player1'})
# if user:
#     # Find scores linked to the user
#     user_scores = scores_collection.find({'user_id': user['_id']})
#     for score in user_scores:
#         print(f"Score: {score['score']} on {score['game_date']}")
# else:
#     print("User not found.")


# import pymongo
# from dotenv import load_dotenv
# import os








# load_dotenv()

# try:
#     mongodb_uri = os.getenv("MONGO_URI")
#     client = pymongo.MongoClient(mongodb_uri)
#     print("Succesfully connected to database")

# except:
#     print("Something went wrong whilest establishing the connection")


    

# db = client.get_database("family_feud")
# users = db.get_collection("users")


# def save_user(user:dict, users):
#     saved_user = users.insert_one(user)
#     return saved_user


# def delete_user(user, users):
#     users.delete_one(user)


# def update_user(user, users):
#     users.update_one(user)

    




