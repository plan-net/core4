import getpass
import os
import shutil
import sys

import pymongo.errors
import yaml

if os.getuid() != 0:
    print("requires root privileges, switch now ...")
    print()
    os.execv(
        "/usr/bin/sudo",
        ["/usr/bin/sudo", sys.executable]
        + sys.argv
        + [
            str(os.getuid()),
            str(os.getgid()),
            os.path.expanduser("~")
        ])

if len(sys.argv) < 2:
    print("must not start local_setup.py as root")
    sys.exit(-1)

HOME = sys.argv[-1]
GID = int(sys.argv[-2])
UID = int(sys.argv[-3])


def ask(prompt, default=None, hide=False):
    if hide:
        resp = getpass.getpass(prompt + ": ")
    else:
        if default:
            print("{} [{}]: ".format(prompt, default), end="")
        else:
            print("{}: ".format(prompt), end="")
        resp = input()
        if resp.strip() == "":
            resp = default
        if default:
            return type(default)(resp)
    return resp


def yn(prompt, default):
    while True:
        print("{} [{}]: ".format(prompt, "yes" if default else "no"), end="")
        resp = input()
        if resp.strip() == "":
            return default
        elif resp.strip().lower() in ("y", "yes"):
            return True
        elif resp.strip().lower() in ("n", "no"):
            return False


print("MongoDB setup")
hostname = ask("  hostname", "localhost")
port = ask("  port", 27017)
auth = yn("  authentication required", False)

print(hostname, port, auth)
if auth:
    username = ask("  username")
    password = ask("  password", hide=True)
    print(username, password)

print("Testing connection ...")
if auth:
    url = "mongodb://{}:{}@{}:{}".format(username, password, hostname, port)
else:
    url = "mongodb://{}:{}".format(hostname, port)
mongo = pymongo.MongoClient(url)
mongo.list_database_names()

opts = mongo.admin.command("getCmdLineOpts")
mongo_config_file = opts["parsed"]["config"]
mongo_config = opts["parsed"]
del mongo_config["config"]
replica = "replication" in opts["parsed"]
if replica:
    replSetName = opts["parsed"]["replication"]["replSetName"]

print("  MongoDB configuration:", mongo_config_file)
print("  mongoDB replication: {}".format(replSetName if replica else "None"))

core_config = {
    "DEFAULT": {
        "mongo_url": url,
        "mongo_database": "core4dev"
    },
    "logging": {
        "mongodb": "INFO"
    }
}

print("running setup")
core_config_path = os.path.join(HOME, ".core4")
core_config_file = os.path.join(core_config_path, "local.yaml")
if not os.path.exists(core_config_path):
    if yn("  create directory [{}]".format(core_config_file), True):
        os.mkdir(core_config_path)
        os.chown(core_config_path, UID, GID)
        open(core_config_file, "w", encoding="utf-8").write(
            yaml.dump(core_config))

mongo_config["replication"] = {
    "oplogSizeMB": 1000,
    "replSetName": "rs0"
}

if not replica:
    if yn("  create MongoDB replica set", True):
        shutil.move(mongo_config_file, mongo_config_file + ".backup")
        open(mongo_config_file, "w", encoding="utf-8").write(
            yaml.dump(mongo_config))
        os.system("service mongodb restart 1>/dev/null 2>&1")
        os.system("sv restart mongodb 1>/dev/null 2>&1")
        os.system("systemctl restart mongod.service 1>/dev/null 2>&1")
        while True:
            mongo = pymongo.MongoClient(url)
            try:
                mongo.list_database_names()
            except pymongo.errors.OperationFailure:
                pass
            else:
                js = {
                    "_id": "rs0",
                    "members": [
                        {
                            "_id": 0,
                            "host": "localhost:27017"
                        }
                    ]
                }
                mongo.admin.command('replSetInitiate', js)
                break

print("done.")
