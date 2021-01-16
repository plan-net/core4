#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from core4.api.v1.request.main import CoreRequestHandler
from core4.api.v1.request.role.model import CoreRole
from bson import ObjectId
from tornado.web import HTTPError
from io import BytesIO
from imghdr import what

MB = 1024 * 1024


class AvatarHandler(CoreRequestHandler):
    """
    Get and Manage Your Avatar.
    """
    MAX_AVATAR_SIZE = 16 * MB  # 16 MB
    VALID_IMAGES = ["png", "jpg", "jpeg", "gif", "bmp"]

    async def get(self):
        """
        get the avatar of the logged in user

        Methods:
            GET /core4/api/v1/avatar

        Parameters:
            None

        Returns:
            Byte stream with content type ``image/jpeg`` or ``data`` response
            with text ``No avatar set yet.``

        Raises:
            401: Unauthorized

        Examples:
            >>> from requests import post
            >>> rv = get("http://localhost:5001/core4/api/v1/avatar")
            <Response [200]>
        """
        _id = self.user._id
        img = await self.config.sys.setting.find_one({"_id": _id},
                                                     {"_id": 0, "avatar": 1})
        if img:
            self.set_header("Content-Type", "image/jpeg")
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
                # todo: should be 500
                self.reply("Your avatar does not seem to be valid. Please try"
                           "uploading a new one.")
            self.set_header("Content-Length", image.getbuffer().nbytes)
            self.write(image.read())
            self.finish()
        else:
            # todo: should be a 404, because this is what it is: not found
            self.reply("No avatar set yet.")

    async def post(self):
        """
        set the users avatar.

        Methods:
            POST /core4/api/v1/avatar

        Parameters:
            file upload with parameter ``file``

        Returns:
            Success message ``Successfully set an avatar.``

        Raises:
            401: Unauthorized
            400: Bad Request (Maximal allowed avatar size)
            400: Bad Request (Please upload a valid image)

        Examples:
            >>> payload={}
            ...     file=[
            ...         ('file',('image.jpeg',
            ...             open('/tmp/image.jpg','rb'), 'image/jpeg'))]
            >>> headers = {
            ...    'Authorization': 'Basic YWRtaW46aGFucw=='
            ... }
            >>> response = requests.request(
            ...     "POST", "http://0.0.0.0:5001/core4/api/v1/avatar",
            ...     headers=headers, data=payload, files=file)
            >>> response
            <Response [200]>
        """
        _id = self.user._id
        file = self.request.files
        if "file" in file:
            bio = BytesIO(file['file'][0]['body'])
            if bio.getbuffer().nbytes > self.MAX_AVATAR_SIZE:
                raise HTTPError(
                    400, "Maximal allowed avatar size is {:1.0f}MB!".format(
                        self.MAX_AVATAR_SIZE / MB))
            if what(bio) in self.VALID_IMAGES:
                await self.config.sys.setting.update_one(
                    {"_id": _id}, {"$set": {"avatar": bio.getvalue()}},
                    upsert=True)
                return self.reply("Successfully set an avatar.")
        raise HTTPError(400, "Please upload a valid image {}".format(
            self.VALID_IMAGES))
