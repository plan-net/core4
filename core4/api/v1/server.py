import core4.api.v1.request.login
import core4.api.v1.request.profile
from core4.api.v1.application import CoreApiContainer, serve


class CoreApiServer(CoreApiContainer):
    root = "core4/api/v1"
    rules = [
        (r"/login", core4.api.v1.request.login.LoginHandler),
        (r"/profile", core4.api.v1.request.profile.ProfileHandler)
    ]


if __name__ == '__main__':
    serve(CoreApiServer)
