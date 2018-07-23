from core4.config import connect

mongo_url = "mongodb://admin:juhu@local3:27017"
mongo_database = "local3db"

account1 = {
    "mongo_database": "comehere",
    "coll1": connect("mongodb://localhost:27028/priv/priv_coll")
}
