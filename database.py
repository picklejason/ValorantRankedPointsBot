import os
import pymongo
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
DATABASE_URI = os.getenv("DATABASE_URI")

client = MongoClient(DATABASE_URI)
db = client["Discord"]
collection = db["profiles"]


def set_player_name(id, name):
    if collection.count_documents({"_id": id}, limit=1) == 0:
        collection.insert_one({"_id": id, "player_name": name})
    else:
        collection.update_one({"_id": id}, {"$set": {"player_name": name}})


def get_player_name(id):
    player_name = collection.find_one({"_id": id}, {"_id": 0, "player_name": 1})
    if player_name is not None:
        return player_name.get("player_name")
    return None


def set_player_id(id, player_id):
    collection.update_one({"_id": id}, {"$set": {"player_id": player_id}})


def get_player_id(id):
    player_id = collection.find_one({"_id": id}, {"_id": 0, "player_id": 1})
    if player_id is not None:
        return player_id.get("player_id")
    return None


def del_player_id(id):
    collection.update_one({"_id": id}, {"$unset": {"player_id": 1}})


def set_track_player(id, player):
    collection.update_one({"_id": id}, {"$set": {"track_player": player}})


def get_track_player(id):
    track_player = collection.find_one({"_id": id}, {"_id": 0, "track_player": 1})
    if track_player is not None:
        return track_player.get("track_player")
    return None


def del_track_player(id):
    collection.update_one({"_id": id}, {"$unset": {"track_player": 1}})


def set_match_id(id, match):
    collection.update_one({"_id": id}, {"$set": {"match_id": match}})


def get_match_id(id):
    match_id = collection.find_one({"_id": id}, {"_id": 0, "match_id": 1})
    if match_id is not None:
        return match_id.get("match_id")
    return None


def get_all_users():
    return collection.find().distinct("_id")
