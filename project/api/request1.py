import tornado.web


class Request1(tornado.web.RequestHandler):

    def get(self):
        return "hello world from "

