===============
feature summary
===============

core4 facilitates the day-to-day tasks of data engineers and data scientists.
The main objective of data engineers is to effectively integrate and deliver
data for analysis and insights. The main objective of data scientists is to
provide relevant insights to business users.

core4 aims to support this community with the technical bits and pieces and to
let them focus on their main objectives: data integration and insight creation.

With the bundling of the following features the core4 framwork reduces time to
market for data management, insight extraction and its business application and
as a consequence  to deliver results to end users in hours or days. Not weeks
or months:

* :ref:`automated job execution <job>` - simple schema to automate, monitor
  and control jobs in a reliable, yet fault tolerant way
* :ref:`scale up (and scale down) <parallel>` - parallel computing mechanic
  from multi-core laptop enviironments to a multi-node cluster setup
* :ref:`project architecture <project>` a unified scheme to package and manage
  multiple projects, accounts, business domains, or tenants
* :ref:`ReST API <api>` - unified interface to access and distribute insights
  and data to exchange data with other systems inbound and outbount including
  web application frameworks
* :ref:`widgets <widget>` as mini applications - extension to the ReST API to
  deliver simple single-page applications
* :ref:`unified authorisation and access management <access>` across
  :ref:`jobs <job>`, :ref:`ReST API <api>`, databases and applications
* :ref:`configuration management <config>` - a flexible configuration system
  which allows an effective transition from analysis and development, through
  testing and staging into production environments; furthermore core4
  configuration mechanics pierce the boundaries between environments and
  provide easy, yet secure access to the most relevant ingredient of data
  engineers' and data scientists' daily business: acces real (production) data
* :ref:`central logging <logging>` - of all core4 activities, actions and
  events; this facilitates troubleshooting, bug fixing and in performance
  analyses in a distributed runtimme environment
* :ref:`simple deployment and rollout mechanic <deploy>` to support the
  *not so technical* data scientist and data engineer in productionising all
  deliverables, results and tools


.. figure:: _static/architecture1.png
   :scale: 65%
   :alt: core4 component overview
