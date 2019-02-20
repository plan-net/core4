#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import re
from tornado.web import HTTPError

import core4
import core4.const
import core4.util
import core4.util.tool
from core4.base.main import CoreBase
from core4.api.v1.request.main import CoreRequestHandler
from core4.api.v1.request.role.model import CoreRole

# ToDo: tornado best approach for path handling

# restriction in resource name for level1
sys_name_restrictions = re.compile('(^[_])')


# error handler interceptor
def handle_errors(func):
    async def call(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HTTPError as error:
            self = args[0]
            if isinstance(self, CoreRequestHandler):
                self.write_error(error.status_code, error=error.reason)
                raise error
    return call


class SettingHandler(CoreRequestHandler):
    """
    Service for storing user setting data which enables the front-end to store user setting data in the database.
    This service cares about user-related system data and project specific settings.

    .. note:: The data should have the next structure:

        level 1 - this resource level holds the system in general related data (favorite widgets, dashboards,
        the widgets in a dashboard) and project related data. System data is stored in a reserved key named “_general”,
        project data can be stored using any other key name. Data for “_general” and projects is stored as “key: value” pairs

        level 2 - this resource level holds directly the data specific to a key described in “level 1”.
        Data is stored by “key: value” pairs structure, where the key is the name of settings property and
        the value is JSON data (string, number, boolean, array, dictionary (JS Object), Base64 encoded binary data)

        Beyond level 2 no restriction in resource structure

    Endpoint structure example:
        core4/api/v1/setting/_general/language?username=jdo
                    \_______\________\________\
                        |    	|        |
           service endpoint  level 1  level 2
    """
    title = "user setting"
    author = "oto"
    protected = True

    default_setting = None

    # ############################################################################################################### #
    # Private methods
    # ############################################################################################################### #

    def _is_resource_name_valid(self, resource):
        if sys_name_restrictions.match(resource):
            # allow user extend existing default_setting with custom key/value
            if resource not in [*self._get_default_setting()]:
                return False
        return True

    def _has_empty_keys(self, recourse_dict):
        return any(key is "" for key in [*recourse_dict])

    def _is_body_structure_valid(self, body):
        if type(body) is not dict:
            return False

        # check level1 resources
        for level1_key, value in body.items():
            # level1 resource name shouldn't be an empty
            if not level1_key:
                return False

            # level1 resource should be a dict
            if type(value) is not dict:
                return False

            # level1 resource name should follow the naming restriction
            if not self._is_resource_name_valid(level1_key):
                return False

            # level2 resource name shouldn't be an empty
            if self._has_empty_keys(value):
                return False

        return True

    def _validate_service_restrictions(self, resources, body):
        length = len(resources)

        if length > 1:                                                              # setting/level1/level2/.../level(n)
            return self._is_resource_name_valid(resources[0])
        elif length == 1:                                                           # setting/level1
            return self._is_resource_name_valid(resources[0]) and type(body) is dict \
                                                              and not self._has_empty_keys(body)
        else:                                                                       # setting/
            return self._is_body_structure_valid(body)

    def _create_nested_dict(self, key_list=None, value=None):
        new_dict = dictionary = {}
        key_list = [] if not key_list else key_list

        for key, has_next in core4.util.tool.has_next(key_list):
            if has_next:
                if key not in dictionary:
                    dictionary[key] = {}
                    dictionary = dictionary[key]
            else:
                dictionary[key] = value

        return new_dict

    def _dict_merge(self, to_dict, from_dict):
        return core4.util.tool.dict_merge(to_dict, from_dict)

    def _get_default_setting(self):
        if self.default_setting is None:
            self.default_setting = self.config.raw_config("user_setting") or {}

        return self.default_setting

    async def _get_user_id(self):
        """
        Grep user unique ID.

        username - query parameter which specifies the user for which the settings should be retrieved.
        Requires COP (core operators) permissions to be used.
        If not provided, settings for the current user are returned.

        :return: string: unique user ID
        """
        username_param = self.get_argument("username", default=None)
        user_details = await self.user.detail()

        if username_param is not None and self.user.is_admin():
            lookup = await CoreRole().find_one(name=username_param)
            detail = await lookup.detail()
            return detail['_id']
        else:
            return user_details['_id']

    async def _get_request_info(self):
        path = self.request.path[len(core4.const.SETTING_URL) + 1:]
        resources = path.split("/") if path else []
        user_id = await self._get_user_id()

        # resource can't be empty. E.g: setting//general
        for name in resources:
            if name == "":
                raise HTTPError(status_code=400, reason="Invalid resource name")

        return [path, resources, user_id]

    async def _get_db_document(self, user_id, merge=False):
        document = await CoreSettingDataAccess().find_one(_id=user_id) or {}

        if merge:
            return self._dict_merge(self._get_default_setting(), document)

        return document

    def _get_body(self):
        body = self.get_argument('data', default=None)

        if not body:
            raise HTTPError(status_code=400, reason="Body in request is empty")

        return body

    def _data_extractor(self, resources, document):
        try:
            for key in resources:
                document = document[key]
        except:
            raise HTTPError(status_code=400, reason="Invalid resource name")

        return document

    # ############################################################################################################### #
    # Request handlers
    # ############################################################################################################### #

    @handle_errors
    async def get(self, *args, **kwargs):
        """
        Get user setting data from database, extend with default system related data from core4.yaml file

        Methods:
            GET /

        Parameters:
            username (str): parameter which specifies the user for which the settings should be retrieved.
            Requires COP (core operators) permissions to be used. If not provided, settings for the current user are returned.

        Returns:
            data element with user-related system data and project specific settings

        Raises:
            400 Bad request: Invalid resource name
        """
        (path, resources, user_id) = await self._get_request_info()
        document = await self._get_db_document(user_id, True)

        self.reply(self._data_extractor(resources, document))

    @handle_errors
    async def delete(self, *args, **kwargs):
        """
        Delete user setting from database

        Methods:
            DELETE /

        Parameters:
            username (str): parameter which specifies the user for which the settings should be retrieved.
            Requires COP (core operators) permissions to be used. If not provided, settings for the current user are returned.

        Returns:
            None

        Raises:
            400 Bad request: Invalid resource name
            400 Bad request: Failed to delete setting - database not able to delete record(s)
            404 Not found: Resource not found - database not able to find user related document
        """
        (path, resources, user_id) = await self._get_request_info()
        delete_db_path = {'.'.join(resources): 1} if resources else None

        await CoreSettingDataAccess().delete(user_id, delete_db_path)

        self.reply({})

    @handle_errors
    async def post(self, *args, **kwargs):
        """
        Create/update user settings in database

        Methods:
            POST /

        Parameters:
            username (str): parameter which specifies the user for which the settings should be retrieved.
            Requires COP (core operators) permissions to be used. If not provided, settings for the current user are returned.

        Returns:
            data element with set data from request body

        Raises:
            400 Bad request: Invalid resource name
            400 Bad request: Body in request is empty - invalid request structure, empty body section
            400 Bad request: Failed to insert setting - database not able to create new user-related document (initial post)
            400 Bad request: Failed to update setting - database not able to update records
        """
        body = self._get_body()
        (path, resources, user_id) = await self._get_request_info()

        if self._validate_service_restrictions(resources, body):
            if len(resources):
                insert_data = self._create_nested_dict(key_list=resources, value=body)
            else:
                insert_data = body
        else:
            raise HTTPError(status_code=400, reason="Invalid resource name")

        document = await self._get_db_document(user_id)

        await CoreSettingDataAccess().save(user_id, self._dict_merge(document, insert_data))

        self.reply(body)

    async def put(self, *args, **kwargs):
        """
        Same as :meth:`.post`
        """
        await self.post(*args, **kwargs)


class CoreSettingDataAccess(CoreBase):
    """
    Encapsulates database access for main http methods: GET, POST, PUT, DELETE
    This class should be used only inside SettingHandler class
    """
    # FIXME: avoid using HTTPError in the database layer
    _collection = None

    @property
    def collection(self):
        if self._collection is None:
            self._collection = self.config.sys.setting.connect_async()

        return self._collection

    async def find_one(self, **kwargs):
        """
        Find user-relevant document in database

        Parameters:
            _id (dict id): user unique id

        Returns:
            user-relevant database document
        """
        cursor = self.collection.find(filter=kwargs, projection={'_id': False})
        db_documents = await cursor.to_list(length=1)

        return db_documents[0] if db_documents else None

    async def save(self, user_id, data):
        """
        Create/update user-relevant document

        Parameters:
            user_id (dict id): user unique id
            data: data that will be used for create/update document

        Returns:
            None

        Raises:
            400 Bad request: Failed to insert setting
            400 Bad request: Failed to update setting
        """
        db_document = await self.find_one(_id=user_id)

        if db_document is None:
            data['_id'] = user_id
            result = await self.collection.insert_one(data)

            if result.inserted_id is None:
                raise HTTPError(status_code=400,  reason="Failed to insert setting")
        else:
            result = await self.collection.update_one(
                filter={"_id": user_id},
                update={"$set": data})

            if result.matched_count == 0:
                raise HTTPError(status_code=400, reason="Failed to update setting")

    async def delete(self, user_id, data=None):
        """
        Delete records/document in database

        Parameters:
            user_id (dict id): user unique id
            data: data that will be used for delete records/document in database

        Returns:
            None

        Raises:
            404 Nor found: Resource not found
            400 Bad request: Failed to delete setting
        """
        db_document = await self.find_one(_id=user_id)

        if db_document is None:
            raise HTTPError(status_code=404, reason="Resource not found")
        else:
            if data:
                result = await self.collection.update_one(
                    filter={"_id": user_id},
                    update={"$unset": data})

                if result.modified_count == 0:
                    raise HTTPError(status_code=404, reason="Resource not found")
            else:
                result = await self.collection.delete_one({"_id": user_id})

                if result.deleted_count == 0:
                    raise HTTPError(status_code=400, reason="Failed to delete setting")
