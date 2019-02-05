import io
import re
import yaml
from pathlib import Path
from tornado.web import HTTPError

import core4
import core4.const
import core4.util
import core4.util.tool
from core4.base.main import CoreBase
from core4.api.v1.request.main import CoreRequestHandler
from core4.api.v1.request.role.model import CoreRole


# ToDo: mongoDB best approach for add, update, delete fields
# ToDo: tornado best approach for path handling
# ToDo: add api tests
# ToDo: improve code readability
# ToDo: add all function description
# ToDo: add needed comments in code
# ToDo: check naming
# ToDo: update documentation/jira


def _read_yaml(file_path):
    """
    Read system configuration from general_setting.yaml file

    :param file_path: str: path to file with configuration
    :return: dict: setting dict
    """
    if file_path.exists():
        with io.open(str(file_path)) as f:
            body = f.read()
        data = yaml.safe_load(body) or {}
        return data
    else:
        raise FileNotFoundError(file_path)


default_setting = _read_yaml(Path(__file__).parent / "general_setting.yaml")

# restriction in resource name for level1
sys_name_restrictions = re.compile('(^[_])')


class SettingHandler(CoreRequestHandler):
    # ToDo: add all needed props
    title = "user settings"
    author = "oto"
    protected = True

    @staticmethod
    def is_resource_name_valid(resource):
        if sys_name_restrictions.match(resource):
            # allow user extend existing default_setting with custom key/value
            if resource not in [*default_setting]:
                return False
        return True

    @staticmethod
    def is_body_structure_valid(body):
        if type(body) is dict:
            # check level1 resources name
            for key in [*body]:
                # level1 resource should be a dict
                if type(body[key]) is not dict:
                    return False

                if sys_name_restrictions.match(key):
                    # allow user extend existing default_setting with custom key/value
                    if key not in [*default_setting]:
                        return False

            return True
        else:
            return False

    def check_restrictions(self, resources, body):
        length = len(resources)

        if length > 1:                                                              # setting/level1/level2/.../level(n)
            return self.is_resource_name_valid(resources[0])
        elif length == 1:                                                           # setting/level1
            return self.is_resource_name_valid(resources[0]) and type(body) is dict
        else:                                                                       # setting/
            return self.is_body_structure_valid(body)

    @staticmethod
    def create_nested_dict(key_list=[], value=None):
        new_dict = dictionary = {}

        for key, has_more in core4.util.tool.lookahead(key_list):
            if has_more:
                if key not in dictionary:
                    dictionary[key] = {}
                    dictionary = dictionary[key]
            else:
                dictionary[key] = value

        return new_dict

    @staticmethod
    def pull_data(resources, data):
        if len(resources):
            try:
                if len(resources) > 1:
                    for resource in resources:
                        if resource in [*default_setting]:
                            data = core4.util.tool.dict_merge(default_setting[resource], data[resource])
                        else:
                            data = data[resource]
                    return data
                else:
                    if resources[0] in [*default_setting]:
                        return core4.util.tool.dict_merge(default_setting[resources[0]], data.get(resources[0]) or {})
                    else:
                        return data[resources[0]]
            except:
                raise HTTPError(status_code=400, reason='Invalid resource name')
        else:
            return core4.util.tool.dict_merge(default_setting, data)

    async def get_user_id(self):
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

    async def get(self, *args, **kwargs):
        path = self.request.path[len(core4.const.SETTING_URL) + 1:]
        resources = path.split("/") if path else []
        user_id = await self.get_user_id()

        document = await CoreSettingDataAccess().find_one(_id=user_id) or {}

        self.reply(self.pull_data(resources, document))

    async def post(self, *args, **kwargs):
        body = self.get_argument('data', default=None)

        if not body:
            raise HTTPError(status_code=400, reason='Body request empty')

        path = self.request.path[len(core4.const.SETTING_URL) + 1:]
        resources = path.split("/") if path else []
        user_id = await self.get_user_id()

        if self.check_restrictions(resources, body):
            if len(resources):
                insert_data = self.create_nested_dict(key_list=resources, value=body)
            else:
                insert_data = body
        else:
            raise HTTPError(status_code=400, reason='Invalid resource name')

        await CoreSettingDataAccess().save(user_id, insert_data)

    async def delete(self, *args, **kwargs):
        path = self.request.path[len(core4.const.SETTING_URL) + 1:]
        resources = path.split("/") if path else None
        user_id = await self.get_user_id()

        if resources:
            await CoreSettingDataAccess().delete(user_id, {resources[-1]: 1})
        else:
            await CoreSettingDataAccess().delete(user_id)

    async def put(self, *args, **kwargs):
        await self.post(*args, **kwargs)


class CoreSettingDataAccess(CoreBase):
    _collection = None

    @property
    def collection(self):
        """
        Open database connection
        :return: async :class:`.CoreCollection` object to ``sys.role``
        """
        if self._collection is None:
            self._collection = self.config.sys.setting.connect_async()
        return self._collection

    async def find_one(self, **kwargs):
        cursor = self.collection.find(filter=kwargs)
        settings = await cursor.to_list(length=1)

        if settings:
            return settings[0]
        else:
            return None

    async def save(self, user_id, data):
        settings = await self.find_one(_id=user_id)

        if settings:
            result = await self.collection.update_one(
                filter={"_id": settings["_id"]},
                update={"$set": data})

            if result.matched_count == 0:
                raise RuntimeError('failed to update settings')
        else:
            data['_id'] = user_id
            result = await self.collection.insert_one(data)

            if result.inserted_id is None:
                raise RuntimeError("failed to insert settings")

    async def delete(self, user_id, data=None):
        settings = await self.find_one(_id=user_id)

        if settings:
            if data:
                result = await self.collection.update_one(
                    filter={"_id": settings["_id"]},
                    update={"$unset": data})

                if result.matched_count == 0:
                    raise RuntimeError('failed to update settings')
            else:
                result = await self.collection.delete_one({"_id": settings["_id"]})

                if result.deleted_count == 0:
                    raise RuntimeError("failed to delete settings")
