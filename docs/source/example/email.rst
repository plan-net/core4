#########################
sending emails with core4
#########################

This example illustrates how to use different Mixins that provide additional
functionality within a CoreJob. Here, the MailMixin located in
``core4/util/email`` is used.

The mixin provides the method ``send_mail()``.
It requires a string or list of recipients, a message (str)
(if the message is in html, one has to set the html=True argument) and a
subject (also str).

The email is configured to use a local MTA without authentication::

    email:
      username: ""
      password: ""
      host: "localhost"
      ssl: False
      sent_from: "core4 e-mail service"
      port: 25

The following Python code creates a CoreJob that checks the availability of a
configured domain every 5 minutes. If the domain is available, it sends an
email to the configured recipient(s)::

    import requests
    import re
    from  core4.error import Core4Error

    class CheckDomain(MailMixin, CoreJob):
        """
        This CoreJob queries the DNS sergice whoisxmlapi and retreives the
        availability of a configured domain every 5 minutes.
        If the domain is available, it sends an email to the configured address.
        """
        author = "mkr"
        schedule = "*/5 * * * *"

        def execute(self, *args, **kwargs):

            try:
                req = requests.get(self.class_config.base_url +
                                   "?apiKey=" + self.class_config.api_key +
                                   "&domainName=" +
                                   self.class_config.domain_name)
            except Exception as e:
                self.logger.critical("Can't contact the configured API.")
                raise e

            if req.status_code == 200:
                try:
                    if req.json()['DomainInfo']['domainAvailability'] == \
                            "AVAILABLE":
                        self.logger.info("The domain {0} is now AVAILABLE!"
                                         .format(self.class_config.domain_name))
                        self.send_mail(to=self.class_config.recipient,
                                       message="The domain {0} is now "
                                               "AVAILABLE!"
                                       .format(self.class_config.domain_name),
                                       subject="core4 domain alert")
                    else:
                        self.logger.info("The domain {0} ist still UNAVAILABLE"
                                         .format(self.class_config.domain_name))
                except Exception as e:
                    raise Core4Error("The API returned an invalid response.")

            else:
                raise Core4Error(("The domain API returned an Error:"
                                  "HTTP Status Code: {0}"
                                  .format(req.status_code)))

The example CoreJob uses the following plugin configuration (given that the
qual_name() of the CoreJob is: "core4.example.CheckDomain")::

    core4:
      example:
        CheckDomain:
          base_url: https://domain-availability-api.whoisxmlapi.com/api/v1
          api_key: very_secret_key
          domain_name: example.com
          recipient: core4-admin@plan-net.com

