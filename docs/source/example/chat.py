"""
chat - simple chat terminal client

Usage:
  chat HOSTNAME USERNAME [PASSWORD] [--ssl]

Options:
  -h --help  Show this screen
  --ssl      use secure protocol (https/wss)
"""

import json
from getpass import getpass
from threading import Thread

from docopt import docopt
from requests import get
from websocket import create_connection


def listening(ws):
    while True:
        data = json.loads(ws.recv())
        if "channel" in data:
            print("{} > {}".format(data["author"], data["data"]))


def main():
    args = docopt(__doc__, help=True)

    if args["PASSWORD"] is None:
        args["PASSWORD"] = getpass("enter password: ")

    LOGIN_URL = "{HOSTNAME:s}/core4/api/login" \
                "?username={USERNAME:s}&password={PASSWORD:s}"
    SOCKET_URL = "{HOSTNAME:s}/core4/api/v1/event?token={token:s}"

    if args["--ssl"]:
        url = "https://"
        ws = "wss://"
    else:
        url = "http://"
        ws = "ws://"

    # login
    login_url = url + LOGIN_URL.format(**args)
    login = get(login_url, verify=False)
    assert login.status_code == 200
    token = login.json()["data"]["token"]
    print("> login")

    # connect
    ws_url = ws + SOCKET_URL.format(token=token, **args)
    ws = create_connection(ws_url)
    assert ws.connected
    print("> web socket connected")

    # announce interest
    ws.send(json.dumps({"type": "interest", "data": ["message"]}))

    thread = Thread(target=listening, args=(ws,))
    thread.start()

    while True:
        message = input()
        ws.send(json.dumps(
            {"type": "message", "channel": "message", "text": message}))

if __name__ == '__main__':
    main()