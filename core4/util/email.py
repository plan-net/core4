#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from core4.queue.job import CoreJob
import jinja2
import os


class MailMixin(object):
    """
    This mixin sends Emails via a preconfigured email-service.
    Tested and supported are a local MTA and googlemail, although other services
    should work fine too.
    For googlemail please allow unsecure application access for your account.

    Configure this mixin via:

    email:
      username: ~
      password: ~
      sent_from: ~
      host: ~
      port: ~
      ssl: ~
      starttls: ~

    If neither a username, nor a password is set, logging in into the mailserver
    is skipped.
    This may occur when talking to a local MTA.

    core4s configuration delegation pattern can be used.

    Send an email by providing:

    message: str
    subject: str
    to: str || list
    html: bool
    """

    def send_mail(self, message=None, subject=None, to=None, html=False):

        try:
            ssl = self.config.email.ssl
            starttls = self.config.email.starttls
            host = self.config.email.host
            email_user = self.config.email.username
            email_password = self.config.email.password
            sent_from = self.config.email.sent_from
            port = self.config.email.port
        except KeyError as e:
            self.logger.critical("e-mail is not completely configured, "
                                 "aborting")
            self.logger.critical("e-mail should have been sent to: " + str(to) +
                                 " with subject: " + str(subject) +
                                 " and message: " + str(message))
            raise e

        # build the email
        msg = MIMEMultipart()
        msg['From'] = sent_from
        msg['Subject'] = subject

        if html:
            msg.attach(MIMEText(message, 'html'))
        else:
            msg.attach(MIMEText(message, 'plain'))

        try:
            if starttls:
                server = smtplib.SMTP(host, port)
                server.starttls()
                server.ehlo()
            elif ssl:
                server = smtplib.SMTP_SSL(host, port)
                server.ehlo()
            else:
                server = smtplib.SMTP(host, port)
                server.ehlo()
            if email_user and email_password:
                server.login(email_user, email_password)
        except Exception as e:
            self.logger.critical("Could not connect to the e-Mail server")
            raise e

        try:
            if isinstance(to, list):
                for i in to:
                        msg['To'] = i
                        server.sendmail(sent_from, i, msg.as_string())
                        self.logger.info("Successfully send e-Mail to: " +
                                         str(i))
            else:
                msg['To'] = to
                server.sendmail(sent_from, to, msg.as_string())
                self.logger.info("Successfully send e-Mail to: " + str(to))
        except Exception as e:
            self.logger.critical("Sending an e-mail failed")
            raise e

        server.close()
        return True


class RoleEmail(MailMixin, CoreJob):
    author = "mkr"

    def execute(self, recipients=None, subject=None, token=None, template=None,
                realname=None, username=None, language="EN"):
        def rel(path):
            return os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                path))
        template_loader = jinja2.FileSystemLoader(
            rel(self.config.email.template.base_dir)
        )
        template_env = jinja2.Environment(loader=template_loader)
        template = template_env.\
            get_template(template)

        message = template.render(
            realname=realname, username=username,
            domain=self.config.email.template[language.lower()]['domain'],
            token=token,
            contact_email=self.config.store.default.contact)

        self.send_mail(to=recipients, subject=subject, message=message)
