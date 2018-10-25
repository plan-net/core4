from core4.api.v1.application import CoreApiContainer, serve


class CoreApiServer(CoreApiContainer):
    root = "core4/api/v1"
    rules = [
    ]


if __name__ == '__main__':
    serve(CoreApiServer)
