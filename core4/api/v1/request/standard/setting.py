#This Source Code Form is subject to the terms of the Mozilla Public
#License, v. 2.0. If a copy of the MPL was not distributed with this
#file, You can obtain one at https://mozilla.org/MPL/2.0/.

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
# ToDo: improve code readability
# ToDo: add all function description
# ToDo: update documentation/jira

# restriction in resource name for level1
sys_name_restrictions = re.compile('(^[_])')


class SettingHandler(CoreRequestHandler):
    # ToDo: add all needed props
    title = "user settings"
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

    def _is_service_restriction_supports(self, resources, body):
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

        for key, has_more in core4.util.tool.lookahead(key_list):
            if has_more:
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
        username_param = self.get_argument('username', default=None)
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

    async def _get_document(self, user_id, merge=False):
        document = await CoreSettingDataAccess().find_one(_id=user_id) or {}

        if merge:
            return self._dict_merge(self._get_default_setting(), document)

        return document

    def _get_body(self):
        body = self.get_argument('data', default=None)

        if not body:
            raise HTTPError(status_code=400, reason='Body in request empty')

        return body

    def _pull_data(self, resources, document):
        try:
            for key in resources:
                document = document[key]
        except:
            raise HTTPError(status_code=400, reason='Invalid resource name')

        return document

    # ############################################################################################################### #
    # Request handlers
    # ############################################################################################################### #

    async def get(self, *args, **kwargs):
        (path, resources, user_id) = await self._get_request_info()
        document = await self._get_document(user_id, True)

        self.reply(self._pull_data(resources, document))

    async def delete(self, *args, **kwargs):
        (path, resources, user_id) = await self._get_request_info()
        delete_db_path = {'.'.join(resources): 1} if resources else None

        await CoreSettingDataAccess().delete(user_id, delete_db_path)

        self.reply({})

    async def post(self, *args, **kwargs):
        body = self._get_body()
        (path, resources, user_id) = await self._get_request_info()

        if self._is_service_restriction_supports(resources, body):
            if len(resources):
                insert_data = self._create_nested_dict(key_list=resources, value=body)
            else:
                insert_data = body
        else:
            raise HTTPError(status_code=400, reason='Invalid resource name')

        document = await self._get_document(user_id)

        await CoreSettingDataAccess().save(user_id, self._dict_merge(document, insert_data))

        self.reply(body)

    async def put(self, *args, **kwargs):
        await self.post(*args, **kwargs)


class CoreSettingDataAccess(CoreBase):
    _collection = None

    @property
    def collection(self):
        if self._collection is None:
            self._collection = self.config.sys.setting.connect_async()

        return self._collection

    async def find_one(self, **kwargs):
        cursor = self.collection.find(filter=kwargs, projection={'_id': False})
        db_documents = await cursor.to_list(length=1)

        return db_documents[0] if db_documents else None

    async def save(self, user_id, data):
        db_document = await self.find_one(_id=user_id)

        if db_document is None:
            data['_id'] = user_id
            result = await self.collection.insert_one(data)

            if result.inserted_id is None:
                raise RuntimeError("Failed to insert setting")
        else:
            result = await self.collection.update_one(
                filter={"_id": user_id},
                update={"$set": data})

            if result.matched_count == 0:
                raise RuntimeError('Failed to update setting')

    async def delete(self, user_id, data=None):
        db_document = await self.find_one(_id=user_id)

        if db_document is None:
            raise RuntimeError("Failed to delete setting")
        else:
            if data:
                result = await self.collection.update_one(
                    filter={"_id": user_id},
                    update={"$unset": data})

                if result.modified_count == 0:
                    raise RuntimeError('Failed to update setting')
            else:
                result = await self.collection.delete_one({"_id": user_id})

                if result.deleted_count == 0:
                    raise RuntimeError("Failed to delete setting")
