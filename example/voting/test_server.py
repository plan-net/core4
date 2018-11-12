from requests import get, post, delete, put
from pprint import pprint


URL = "http://localhost:5001/voting/v1"

def register():
    rv = post(
        URL + "/register",
        json={
            "token": "secret_token",
            "_id": "mra"
        }
    )
    print(rv.json())


def create_session(question, data={}):
    rv = post(
        URL + "/session",
        json={
            "token": "secret_token",
            "question": question,
            "data": data
        }
    )
    print(rv.json())


#register()
#create_session("Are you important", data={"tag": "test"})

def listing():
    rv = get(URL + "/session", json={"token": "secret_token"})
    pprint(rv.json())

def detail(sid):
    rv = get(URL + "/session/" + sid, json={"token": "secret_token"})
    pprint(rv.json())

def open_session(sid):
    rv = post(URL + "/start/" + sid, json={"token": "secret_token"})
    pprint(rv.json())


sid = "5be8ad3bde8b694326bce5ff"
listing()
detail(sid)

#open_session(sid)

def create_session2():
    rv = post(
        URL + "/session",
        json={
            "token": "secret_token",
            "question": "Another question?",
        }
    )
    pprint(rv.json())


#create_session2()
listing()

sid2 = "5be8ae65de8b694326bce642"
#open_session(sid)
#open_session(sid)
listing()


def close_session(sid):
    rv = post(
        URL + "/stop/" + sid,
        json={
            "token": "secret_token"
        }
    )
    pprint(rv.json())

#close_session(sid)
#listing()
detail(sid)

def event(id, data={}):
    rv = post(
        URL + "/event",
        json={
            "id": id,
            "token": "secret_token",
            "data": data
        }
    )
    pprint(rv.json())

#event("mra")

#create_session("My final question")
#open_session("5be958b8de8b6975631ff7f0")
#listing()

#event("mra")
#event("bzi1")



#open_session("5be958b8de8b6975631ff7f0")
#event("mra2")
event("bzi2")

#close_session("5be958b8de8b6975631ff7f0")
