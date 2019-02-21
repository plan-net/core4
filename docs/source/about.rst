###########
about core4
###########

.. todo: write about how core4 was invented and about the name "core" and "core4"

* history reaches back to 2003 when first experience with distributed, scalable
  reporting systems has been made for Deutsche Börse
* have been variants with databases as the messaging layer as well as pure
  messaging systems as well as client/server network messaging
* with the evolution of no sql databases and esp. couchdb and mongodb a new
  approach to provide a such a data engineering/data science system was taken
* 2014 we started to build all lessons learned from the past 10 years into the
  PN BI core system
* was not a pure product development from the very beginning, but has been
  developed together with clients and on actual client projects
* core version 1 was prototype of data integration and automation system
* core version 2 was the first production version with major improvements
  on job distribution and the worker model
* core version 3 was the extension with ReST API and widgets
* core version 4 is the Python 3 ported version completely rebuilt

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

Basically, every company and team build its own. So did we but with the focus
to provide one goto place for 3 communities: data engineers, scientists and
business users. Everybody is talking about data scientists, but actuall it is
the community of all three which make the difference
(https://www.bigdata-insider.de/analytics-und-bi-das-sind-die-trends-2018-a-668138/,
besonders Punkt 8)

* https://de.slideshare.net/BigDataSpain/importance-of-collaboration-among-programmers-and-data-scientists-by-rafael-del-hoyo-jorge-vea-at-big-data-spain-2015

Just buy a solution still does not deliver all requirements
(https://www.datavard.com/en/blog-why-almost-every-sap-hana-needs-a-data-management-solution/).

And finally there is a lot of buzz and noise around. Consultants like gartner
try to structure the field. But they demonstrate high uncertainty and another
significant symptom is: Pyhon is not part of the story.
(https://www.kdnuggets.com/2018/02/gartner-2018-mq-data-science-machine-learning-changes.html)

We built a system to work with Python. We provide features which make the life
easier (see feature.rst).

So what is core? Some say
* it is a data science platform
* it is a ai platform
* it is a data integration platform
* it is a web app prototyping platform
* it is a production system

we say: it is a swiss knife. Not by itself but through the power of python.
And core4 delivers this swiss army knife with protectors to be used by the not
so skilled data engineer whos focus is data, by the data sientist whos focus
is analysis, by the fe developer whos focus is the usabililty. It is the platform
with agililty in mind to collaborate with the business user whos focus is on the
use case and value add.
