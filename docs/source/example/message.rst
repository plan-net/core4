##################
message processing
##################

Message processing is supported with core4 endpoint ``/core4/api/v1/event``.
See also :doc:`event`. The default channel for chat messages is ``message``.

The following example demonstrates the messaging system with two users
_user1_ and _user2_. Two follow the example you will have to open two dedicated
terminals and enter the core4 environment.

preparation
===========

First you will have to create two users.

.. code-block:: python

    from requests import post, get

    # login as admin
    login = get("http://devops:5001/core4/api/login?username=admin&password=hans")
    token = login.json()["data"]["token"]
    # create user1
    rv = post("http://devops:5001/core4/api/v1/roles",
              headers={"Authorization": "Bearer " + token},
              json={
                  "name": "user1",
                  "realname": "Test User 1",
                  "email": "test1@plan-net.com",
                  "password": "very secret",
                  "role": ["standard_user"]
              })
    assert rv.status_code == 200
    # create user2
    rv = post("http://devops:5001/core4/api/v1/roles",
              headers={"Authorization": "Bearer " + token},
              json={
                  "name": "user2",
                  "realname": "Test User 2",
                  "email": "test2@plan-net.com",
                  "password": "very secret",
                  "role": ["standard_user"]
              })
    assert rv.status_code == 200


Verify both users exists with the role endpoint.

.. code-block:: python

    rv = get("http://devops:5001/core4/api/v1/roles",
              headers={"Authorization": "Bearer " + token})


To simulate a chat between both users, open two terminals and start the simple
terminal chat client script.

.. literalinclude:: chat.py


Before starting the script, ensure the :class:`.CoreApiServer` is up and
running with::

    cd core4
    source enter_env
    python core4/api/v1/server.py


In a second terminal, start the script for _user1_ with::

    cd docs/source/example
    python chat.py devops:5001 user1 "very secret"

In a third terminal, start the script for _user2_ with::

    cd docs/source/example
    python chat.py devops:5001 user2 "very secret"
