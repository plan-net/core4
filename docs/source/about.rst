#############
about core4os
#############

The history of core4os reaches back to 2003 when the first contact with a
distributed and scalable reporting system has been made for the Deutsche Börse
AG.

There were many experiments of different messaging systems for such a system,
ranging from databases as messaging layer to pure messaging services/systems
and client/server network messaging solutions.

With the emersion and rapid evolution of nosql databases, especially couchdb and
mongodb, a new approach to such a data engineering/science system was possible
and approached.

Beginning 2014 we started to build the PN BI core system while incorporating
all the lessons learned from the past ten years of experience.
The development wasn't in a pure product development cycle in the traditional
sense from the beginning, but rather has been developed in tandem with clients on
actual projects.

This development lead to many features being added over time. This resulted in
a version bump every time there were enough new features added to justify a
new version.

* Core v1 was a prototype for a data integration and automation system.
* Core v2 was the first production version with major improvements to the job
  distribution and worker model.
* Core v3 included the addition of a REST Api and Widgets.
* Core v4 is the Python 3 ported version that has been completely rebuilt.

There has been some own research on existing projects. The spectrum on
batch, distributed execution, intensive computations etc. is wide:

* RQ and celery

  * https://de.slideshare.net/sylvinus/why-and-how-pricing-assistant-migrated-from-celery-to-rq-parispy-2
* Queues in general

  * http://queues.io/

* https://engarde.readthedocs.io/en/latest/index.html
* http://conference.scipy.org/proceedings/scipy2012/tom_bertalan.html
* http://conference.scipy.org/proceedings/scipy2013/arya.html
* http://conference.scipy.org/proceedings/scipy2013/krishnan.html
* http://conference.scipy.org/proceedings/scipy2014/clark.html
* http://conference.scipy.org/proceedings/scipy2017/klaus_greff.html
* http://conference.scipy.org/proceedings/scipy2009/paper_6/
* NSQ MIT
* Gearman BSD
* PyRes MIT
* Amazon SQS
* luigi APACHE LICENSE 2.0
* Parallel python
* Ipython take

The gist is, every company and team build its own. So did we but with the focus
to provide one hub and to unify 3 communities: data engineers, scientists and
business users. Everybody is talking about data scientists, but in reality it is
the community of all three that make the difference
(https://www.bigdata-insider.de/analytics-und-bi-das-sind-die-trends-2018-a-668138/,
especially item 8, german!)

* https://de.slideshare.net/BigDataSpain/importance-of-collaboration-among-programmers-and-data-scientists-by-rafael-del-hoyo-jorge-vea-at-big-data-spain-2015

A commercial package solution that seems to deliver everything needed, doesn't
meet all the requirements
(https://www.datavard.com/en/blog-why-almost-every-sap-hana-needs-a-data-management-solution/).

And finally there is a lot of buzz and noise around Data Science. Consultants
like gartner try to structure the field. But they demonstrate high uncertainty
and another significant flaw is that Python is not part of the story.
(https://www.kdnuggets.com/2018/02/gartner-2018-mq-data-science-machine-learning-changes.html)

We built a system to work with Python.
We a system which provides features to make life easier (see feature.rst).

So what is core? Some say

* it is a data science platform
* it is a ai platform
* it is a data integration platform
* it is a web app prototyping platform
* it is a production system

we say: it is a swiss knife. Not by itself but through the power of python and
the expansive eco system python brings with it.
And core4os delivers this swiss army knife with protectors to be used by the not
inexperienced data engineer who focuses on data, by the data scientist who
focuses on analysis, by the Front End developer who focuses on the usability.
It is a platform with agility in mind to collaborate with the business user who
has his focus on specific use cases and adding value to businesses.

**Why Open Source?**

Core was developed with Python 2, the support for Python 2 ends in 2020.
With that many packages stop the support for Python 2 as well.
That's why a migration to Python 3 was unavoidable. And because a migration to
Python 3 would've meant to look at every piece of code regardless, we took this
as a chance to completely rebuild core to get rid of the technical debt
accumulated over the development cycles of cores versions 1 through 3.

**But why make core open source then?**

We are using open source software on a daily basis and are very fond of the
open source mindset. That's why we want to give something back by making the
tool we've worked and developed with in the past years, open source, so more
people have the ability to access and build things themselves with it.

It is also a way for us to increase our transparency, which is a important
aspect of IT security, more eyes on something mean that bugs and flaws can
be found faster and therefore fixed faster. It's also a way for us to get
help in terms of development and to develop core more quickly and more robust.

Since we are quite a small company, ensuring business continuity for our
customers is also a big reason. With core open source it gives customers the
needed security and flexibility.