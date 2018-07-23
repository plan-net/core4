from core4.config import connect

account1 = {
    "mongo_database": "acc1db",
    "coll1": connect("mongodb://localhost/db/testcoll"),
    "coll2": connect("mongodb://localhost/db/testcoll")
}

def x():
    return "bla"
