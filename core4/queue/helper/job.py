import datetime as dt
import requests
import tornado.template

import core4.util
from core4.queue.job import CoreJob
import core4.const


class DummyJob(CoreJob):
    """
    This is just a job-dummy for testing purposes.
    """
    author = 'mra'

    def execute(self, *args, **kwargs):
        import time
        sleep = kwargs.get("sleep", None) or 3
        until = core4.util.node.now() + dt.timedelta(seconds=sleep)
        self.logger.info("just sleeping [%s] seconds", sleep)
        n = 0
        while core4.util.node.now() <= until:
            n += 1
            print("line %d at %s" % (n, core4.util.node.now()))
            p = float(
                sleep - (until
                         - core4.util.node.now()).total_seconds()) / sleep
            self.progress(p, "running")
            time.sleep(0.5)


class MailerJob(CoreJob):
    """
    This job takes the template location (absolute path), recipients, subject
    line and any additional arguments and sends an email.
    """
    author = 'mra'

    def execute(self, template, recipients, subject, *args, **kwargs):
        msg = []
        if not isinstance(recipients, list):
            recipients = [recipients]
        msg.append("FROM: ?")
        msg.append("TO: %s" % (", ".join(recipients)))
        msg.append("SUBJECT: %s" % (subject))
        msg.append("")
        t = tornado.template.Template(template)
        kwargs["recipients"] = ", ".join(recipients)
        kwargs["subject"] = subject
        for k, v in kwargs.items():
            msg.append("variable %s = %s" % (k, v))
        msg.append(t.generate(**kwargs).decode("utf-8"))
        print("\n".join(msg))
        self.logger.debug("send mail:\n%s", "\n".join(msg))


class ApiJob(CoreJob):
    """
    This job visits all API servers which have registered in ``sys.api`` and
    extracts its request handlers into ``sys.handler``.
    """
    author = 'mra'

    def execute(self, *args, **kwargs):
        now = core4.util.node.mongo_now()
        username = self.config.api.admin_username
        password = self.config.api.admin_password
        verify = self.config.api.verify_ssl
        timeout = 1
        self.reset_visit()
        for url in self.visit():
            data = self.extract_widget(url, now,
                                       username, password, verify, timeout)
            for widget in data:
                base = widget.copy()
                del base["route"]
                for route in widget["route"]:
                    route.update(base)
                    route["full_url"] = "{protocol:s}://" \
                                        "{host:s}{url:s}".format(**route)
                    self.logger.debug("collected [%s] with [%s]",
                                      route["url"], route["qual_name"])
                    self.update_widget(route, now)

    def update_widget(self, route, now):
        route["visited"] = now
        self.config.sys.handler.update_one(
            filter={
                "full_url": route["full_url"],
            },
            update={
                "$set": route
            },
            upsert=True
        )

    def reset_visit(self):
        app = self.config.sys.app.update_many(
            filter={},
            update={
                "$set": {
                    "visited": None,
                }
            })
        handler = self.config.sys.handler.update_many(
            filter={},
            update={
                "$set": {
                    "visited": None,
                }
            })
        self.logger.info("reset [%d] app server, [%d] routes",
                         app.modified_count, handler.modified_count)

    def visit(self):
        for doc in self.config.sys.app.find():
            base_url = doc["_id"]
            yield base_url

    def extract_widget(self, url, now, username, password, verify=True,
                       timeout=1):
        info_url = url
        if info_url.endswith("/"):
            info_url = info_url[:-1]
        info_url += core4.const.INFO_URL
        try:
            rv = requests.get(info_url, auth=(username, password),
                              verify=verify, timeout=timeout)
        except Exception as exc:
            self.logger.error("local api collection [%s] failed: %s",
                              info_url, exc)
        else:
            if rv.status_code != 200:
                self.logger.error("local api collection [%s] failed",
                                  info_url)
            else:
                data = rv.json()["data"]["collection"]
                self.logger.info(
                    "local api collection [%s] succeeded with [%d] routes",
                    info_url, len(data))
                self.mark_visit(url, now)
                return data
        return []

    def mark_visit(self, url, now):
        self.config.sys.app.update_one(
            filter={
                "_id": url
            },
            update={
                "$set": {
                    "visited": now
                }
            }
        )


if __name__ == '__main__':
    from core4.queue.helper.functool import execute

    execute(ApiJob)
