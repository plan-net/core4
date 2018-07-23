from core4.config import connect

mongo_database = "core4test"
extra_global = 666

account1 = {
    "a": 0,
    "coll1": connect("mongodb://coll1"),
    "coll2": connect("mongodb://extra1db2/coll2"),
    "deep": {
        "deeper": {
            "deepest": 123
        }
    }
}

account2 = {
    "mongo_database": "extra2db1",
    "mongo_url": "mongodb://core:654321localhost:27018",
    "coll1": connect("mongodb://coll3"),
    "coll2": connect("mongodb://extra2db2/coll4")
}

env1 = {
    "k1": "xyz",
    "k2": None,
    "k3": "unset1",
    "k4": "unset2"
}