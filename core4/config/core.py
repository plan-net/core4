
from core4.config import connect

mongo_url = "mongodb://localhost:27017"  # default mongo connection
mongo_database = "core4dev"  # default core4 system mongo database

kernel = {
    "sys.conf": None,
    "sys.log": None
}

folder = {
    'root': '/srv/core4',
    'transfer': 'transfer',
    'process': 'proc',
    'archive': 'arch',
    'location': 'api/location',
    'upstream': 'api/upstream',
    'vassal': 'api/vassal',
    'temp': 'temp'
}

logging = {
    "stderr": "INFO",
    "stdout": None,
    "mongodb": "DEBUG",
    "format": "%(asctime)s - %(levelname)-8s: %(message)s",
    "memory": {
        "capacity": 1000000,  # log message stack
        "flush": "ERROR",  # if this level is logged, then flush memory
        "emit": "DEBUG"  # spit out all log messages with this level and above
    },
    "extra": None
}
