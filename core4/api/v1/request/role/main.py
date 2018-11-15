import pymongo.errors
from bson.objectid import ObjectId
from tornado.web import HTTPError

import core4.error
from core4.api.v1.request.main import CoreRequestHandler
from core4.api.v1.request.role.model import CoreRole


class RoleHandler(CoreRequestHandler):
    title = "role and user management"
    author = "mra"

    async def post(self, _id=None):
        kwargs = dict(
            name=self.get_argument(
                "name", as_type=str),
            realname=self.get_argument(
                "realname", as_type=str, default=""),
            is_active=self.get_argument(
                "is_active", as_type=bool, default=True),
            role=self.get_argument(
                "role", as_type=list, default=[]),
            email=self.get_argument(
                "email", as_type=str, default=None),
            password=self.get_argument(
                "password", as_type=str, default=None),
            perm=self.get_argument(
                "perm", as_type=list, default=[])
        )
        try:
            role = CoreRole(**kwargs)
            await role.save()
        except (AttributeError, TypeError, core4.error.Core4ConflictError,
                core4.error.ArgumentParsingError) as exc:
            raise HTTPError(400, exc.args[0])
        except pymongo.errors.DuplicateKeyError:
            raise HTTPError(400, "name or email exists")
        except core4.error.Core4RoleNotFound as exc:
            raise HTTPError(400, "role [%s] not found", exc.args[0])
        except:
            raise
        else:
            self.reply(role.to_response())

    async def get(self, _id):
        if _id.strip() == "":
            ret = await CoreRole().load(
                per_page=self.get_argument(
                    "per_page", as_type=int, default=10),
                current_page=self.get_argument(
                    "page", as_type=int, default=0),
                query_filter=self.get_argument(
                    "filter", as_type=dict, default={}),
                sort_by=self.get_argument(
                    "sort", as_type=str, default="_id"),
                sort_order=self.get_argument(
                    "order", as_type=int, default=1),
            )
            for doc in ret.body:
                doc.pop("password", None)
            self.reply(ret)
        else:
            oid = self.parse_objectid(_id)
            ret = await CoreRole().find_one(_id=oid)
            if ret is None:
                raise HTTPError(404, "role [%s] not found", oid)
            self.reply(await ret.detail())

    async def put(self, _id):
        oid = self.parse_objectid(_id)
        ret = await CoreRole().find_one(_id=oid)
        if ret is None:
            raise HTTPError(404, "role [%s] not found", oid)
        kwargs = dict(
            etag=self.get_argument(
                "etag", as_type=ObjectId),
            name=self.get_argument(
                "name", as_type=str, default=None),
            realname=self.get_argument(
                "realname", as_type=str, default=None),
            is_active=self.get_argument(
                "is_active", as_type=bool, default=None),
            role=self.get_argument(
                "role", as_type=list, default=None),
            email=self.get_argument(
                "email", as_type=str, default=None),
            password=self.get_argument(
                "password", as_type=str, default=None),
            perm=self.get_argument(
                "perm", as_type=list, default=None)
        )
        for k, v in kwargs.items():
            if v is not None:
                ret.data[k].set(v)
        try:
            saved = await ret.save()
        except (AttributeError, TypeError, core4.error.Core4ConflictError,
                core4.error.ArgumentParsingError) as exc:
            raise HTTPError(400, exc.args[0])
        except pymongo.errors.DuplicateKeyError:
            raise HTTPError(400, "name or email exists")
        except core4.error.Core4RoleNotFound as exc:
            raise HTTPError(400, "role [%s] not found", exc.args[0])
        except:
            raise
        else:
            if saved:
                self.reply(ret.to_response())
            else:
                self.reply("no changes")

    async def delete(self, _id):
        oid = self.parse_objectid(_id)
        ret = await CoreRole().find_one(_id=oid)
        etag = self.get_argument("etag", as_type=ObjectId)
        if ret is None:
            raise HTTPError(404, "role [%s] not found", oid)
        ret.data["etag"].set(etag)

        try:
            removed = await ret.delete()
        except (AttributeError, TypeError, core4.error.Core4ConflictError,
                core4.error.ArgumentParsingError) as exc:
            raise HTTPError(400, exc.args[0])
        except core4.error.Core4RoleNotFound as exc:
            raise HTTPError(400, "role [%s] not found", exc.args[0])
        except:
            raise
        else:
            if removed:
                self.reply(True)
            else:
                self.reply(False)


