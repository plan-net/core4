from core4.config import connect

mongo_url = "mongodb://core:654321@localhost:27017"
mongo_database = "core4test"

sys = {
    "conf": connect("mongodb://sys.conf")
}