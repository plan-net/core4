.. _http_api:

####################
HTTP API
####################

setting
#######
Core4 provides a RESTful API service for storing user setting data which
enables the front-end to store user setting data in the database.
This service cares about user-related system data and project specific settings.

============== ================================================================
 **level 1** - this resource level holds the system in general related data
               (*favorite apps, dashboards, the apps in a dashboard*) and
               project related data. System data is stored in a reserved key
               named “_general”, project data can be stored using any other
               key name. Data for “_general” and projects is stored as
               **“key: value”** pairs.

 **level 2** - this resource level holds directly the data specific to a key
               described in **“level 1”**. Data is stored by **“key: value”**
               pairs structure, where the key is the name of settings property
               and the value is JSON data (*string, number, boolean, array,
               dictionary (JS Object), Base64 encoded binary data*).
============== ================================================================

**Beyond level 2 no restriction in resource structure.**

Endpoint structure example:
 *core4/api/v1/setting/_general/language?username=jdo*

 ================= ===============================
         *setting* service endpoint
        *_general* **level 1**
        *language* **level 2**
 ================= ===============================


Supported query parameters:

============== =========================================== ====================
Parameter name Description                                 Possible values
============== =========================================== ====================
      username Specifies the user for which the settings   Fully qualified
               should be retrieved. Requires **COP** (core user login name
               operators) permissions to be used. If not
               provided, settings for the current user are
               returned. Applicable for all request types.
============== =========================================== ====================


Resource name restriction:

================ =========================================== ==================
Resource name    Description                                 Rights
================ =========================================== ==================
   (_) character Resource name can’t start with the (_)sign. ✘ - not allowed
                 Fields name which start with an underscore
                 are core4 reserved names and represent
                 core4 system related data
(null) character Resource name can’t contain the (null)      ✘ - not allowed
                 character
          string E.g.: “media_report”, “campaign_1981118594” ✓ - allowed
================ =========================================== ==================


Resource naming convention:

================ ==============================================================
Resource name    Description
================ ==============================================================
             (_) Separate words in resource name with an underscore:
                 “media_report”. Use lowercase for name identifiers.
 symbols in name Resource name shouldn’t contain symbols:  “media.report”,
                 “media#report”, “media!report” etc
          number Resource name shouldn’t start with a number or define only
                 number name: “123campaign”, “123456” etc
================ ==============================================================


JSON request/response structure has the following constraints:

================ ==================================== =========================
Field name       Description                          Type
================ ==================================== =========================
            data Data entry point, will contain the   **JSON data**: string,
                 requested settings tree              number, boolean, array,
                                                      dictionary (JS Object),
                                                      Base64 encoded binary
                                                      data
        _general Data entry point, will contain the   Dictionary (*JS Object*)
                 requested settings tree
  <setting_name> Setting name key                     **JSON data**
  <project_name> Project name key                     Dictionary (*JS Object*)
  <setting_name> Setting name key                     **JSON data**
================ ==================================== =========================

JSON request/response structure example::

    {
    <request system info: _id, code, error,  message, timestamp >,
    data: {
        _general: {
            setting_name(1): <json_data>,
            ...
            setting_name(n): <json_data>,
        },
        project_name(1): {
            setting_name(1): <json_data>,
            ...
            setting_name(n): <json_data>
        },
        ...
        project_name(n): {
            setting_name: <json_data>
        }
    }


Resource query restriction:
    - there is no possibility query inside an array:
         /core4/api/v1/setting/media_reporting/campaign_1981118594
         /``headers[2]``/text

Expected Errors:
    - Invalid resource name - ``400``
    - Resource not found - ``404``
    - Body in request is empty - ``400``
    - Failed to delete setting - ``400``
    - Failed to update setting - ``400``
    - Failed to insert setting - ``400``

POST
======
Create user setting (*Client → Server*)

Endpoint (hierarchical structure):
    */setting/<?project_name | _general>/<?setting_name>/<?json_key>/...
    /<?json_key>*

Create requests::

        Request URL: /setting
        Request Method: POST
        Content-Type: application/json
        Accept: application/json
        ---- standard headers ----
        Request body:
        {
            "data": {
                “_general”: { ←system related user data
                    “language”: ”ENG”
                },
                "media_reporting": {   ← project name
                    "campaign_1981118594": {   ← setting name
                        "headers": [  ← json data
                            {
                                "text": "Kunde",
                                "value": "client",
                                "format": "",
                                "selected": true
                            },
                            {
                                "text": "Kampagne",
                                "value": "campaign_name",
                                "format": "",
                                "selected": true
                            }
                         ]
                    }
                }
            }
        }

Create successful response::

    Status: 200 <OK>
    Response body:
    {
        “_id”: “5bd94d9bde8b6939aa31ad88”,
        “code”: 200,
        “data”: {
           “_general”: {
                “language”: ”ENG”
            },
            "media_reporting": {
                "campaign_1981118594": {
                    "headers": [
                        {
                            "text": "Kunde",
                            "value": "client",
                            "format": "",
                            "selected": true
                        },
                        {
                            "text": "Kampagne",
                            "value": "campaign_name",
                            "format": "",
                            "selected": true
                        }
                     ]
                }
            }
        },
        “message”: “OK”,
        “timestamp”: “2019-01-28T06:37:15.734609”
    }

Create ``error`` response::

    Status: 400 <Bad request> | 403 <Forbidden> |  500 <Internal server error>
    Response body:
    {
        “_id”: ”5be2d1fcde8b69105ee8b35b”,
        “code”: 400,
        “message”: “Bad request”,
        “error”: “Invalid resource name”,
        “timestamp”: “2019-01-28T11:52:28.682515”
    }

GET
======
Read user setting (*Client → Server*)

Endpoint (hierarchical structure):
    */setting/<?project_name | _general>/<?setting_name>/<?json_key>/...
    /<?json_key>*

Read requests::

        Request URL: setting/media_reporting
        Request Method: GET
        Accept: application/json
        ---- standard headers ----

Read successful response::

    Status: 200 <OK>
    Response body:
    {
        “_id”: “5bd94d9bde8b6939aa31ad88”,
        “code”: 200,
        "data": {
            "campaign_1981118594": {   ← setting name
                "headers": [   ← json data
                    {
                        "text": "Kunde",
                        "value": "client",
                        "format": "",
                        "selected": true
                    },
                    {
                        "text": "Kampagne",
                        "value": "campaign_name",
                        "format": "",
                        "selected": true
                    }
                ]
            }
        },
        “message”: “OK”,
        “timestamp”: “2019-01-28T06:37:15.734609”
    }


Read ``error`` response::

    Status: 400 <Bad request> | 403 <Forbidden> |  500 <Internal server error>
    Response body:
    {
        “_id”: ”5be2d1fcde8b69105ee8b35b”,
        “code”: 400,
        “message”: “Bad request”,
        “error”: “Invalid resource name”,
        “timestamp”: “2019-01-28T11:52:28.682515”
    }


DELETE
======
Remove user setting (*Client → Server*)

Endpoint (hierarchical structure):
    */setting/<?project_name | _general>/<?setting_name>/<?json_key>/...
    /<?json_key>*

Remove requests::

        Request URL: setting/media_reporting/campaign_1981118594/headers
        Request Method: DELETE
        Accept: application/json
        ---- standard headers ----

Remove successful response::

    Status: 200 <OK>
    Response body:
    {
        “_id”: “5bd94d9bde8b6939aa31ad88”,
        “code”: 200,
        “data”: “{}”,
        “message”: “OK”,
        “timestamp”: “2019-01-28T06:37:15.734609”
    }

Remove ``error`` response::

    Status: 400 <Bad request> | 403 <Forbidden> |  500 <Internal server error>
    Response body:
    {
        “_id”: ”5be2d1fcde8b69105ee8b35b”,
        “code”: 400,
        “message”: “Bad request”,
        “error”: “Invalid resource name”,
        “timestamp”: “2019-01-28T11:52:28.682515”
    }

PUT
======
Update user setting (*Client → Server*)

Endpoint (hierarchical structure):
    */setting/<?project_name | _general>/<?setting_name>/<?json_key>/...
    /<?json_key>*

Update requests::

        Request URL: setting/_general/language
        Request Method: PUT
        Content-Type: application/json
        Accept: application/json
        ---- standard headers ----
        Request body:
        {
            "data": ”UA”
        }

Update successful response::

    Status: 200 <OK>
    Response body:
    {
        “_id”: “5bd94d9bde8b6939aa31ad88”,
        “code”: 200,
        “data”: “UA”,
        “message”: “OK”,
        “timestamp”: “2019-01-28T06:37:15.734609”
    }

Update ``error`` response::

    Status: 400 <Bad request> | 403 <Forbidden> |  500 <Internal server error>
    Response body:
    {
        “_id”: ”5be2d1fcde8b69105ee8b35b”,
        “code”: 400,
        “message”: “Bad request”,
        “error”: “Failed to update setting”
        “timestamp”: “2019-01-28T11:52:28.682515”
    }



