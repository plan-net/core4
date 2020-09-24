from core4.api.v1.request.main import CoreRequestHandler
from core4.api.v1.request.role.model import CoreRole
from bson import ObjectId
from tornado.web import HTTPError
from io import BytesIO
from imghdr import what


class AvatarHandler(CoreRequestHandler):
    """
    Get and manage your avatar.
    """
    MAX_AVATAR_SIZE = 16*1024*1024  #16 MB
    VALID_IMAGES = ["png", "jpg", "jpeg", "gif", "bmp"]

    async def get(self, *args, **kwargs):
        """
        get the Avatar of a specific user-id
        """
        user = await CoreRole().find_one(name=self.current_user)
        _id = user._id

        img = await self.config.sys.setting.find_one({"_id": _id},
                                                     {"_id": 0, "avatar": 1})
        if img:
            self.set_header("Content-Type", "image/gif")
            self.set_header("Pragma", "no-cache")
            self.set_header("Cache-Control",
                        "no-store, "
                        "no-cache=Set-Cookie, "
                        "proxy-revalidate, "
                        "max-age=0, "
                        "post-check=0, pre-check=0"
                        )
            try:
                image = BytesIO(img["avatar"])
            except:
                self.reply("Your avatar does not seem to be valid. Please try"
                           "uploading a new one.")
            self.set_header("Content-Length", image.getbuffer().nbytes)
            self.write(image.read())
            self.finish()
        else:
            self.reply("No avatar set yet.")

    async def post(self):
        """
        set the users avatar.
        accessable by either the user itself or an admin
        :return:
        """
        user = await CoreRole().find_one(name=self.current_user)

        _id = user._id

        file = self.request.files
        bio = BytesIO(file['avatar'][0]['body'])

        if bio.getbuffer().nbytes > self.MAX_AVATAR_SIZE:
            raise HTTPError("Maximal allowed avatar size is 16MB!")

        if not what(bio) in self.VALID_IMAGES:
            raise HTTPError("Please upload a valid image.")
        await self.config.sys.setting.update_one({"_id": _id},
                                                 {"$set":
                                                     {"avatar": bio.getvalue()}
                                                 }, upsert=True)
        self.reply("Successfully set an avatar.")

