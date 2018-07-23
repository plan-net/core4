from core4.config import connect

mongo_url = "mongodb://core:654321@localhost:27017"

account1 = {
    "a": 1
}

account2 = {
    "mongo_database": "extra2db3",
    "coll2": connect("mongodb://coll5")
}

env1 = {
    "k3": None
}