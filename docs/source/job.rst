CoreJob
=======


Job principles
------------------------

core4 Jobs represent single or multiple Tasks that are to be executed within the Framework.
Jobs give access to the core4 configuration, core4 queue and the database.

.. _philosophy:

With the core automation framework we adhere to the following two design paradigms:

#. **divide and conquer** - objective is always to break down a job into two or more jobs until these become
   simple enough to be solved directly.
#. **do one thing and do it well**

Both guidelines are interrelated. The *dotadiw* (do one thing and do it well) philosophy is borrowed from the general
Unix philosophies. Actually, the design of automation jobs should follow the first four out of nine guidelines.

* **Small is beautiful.**
* **Make each program do one thing well.**
* **Build a prototype as soon as possible.**
* **Choose portability over efficiency.**


Out of experience we would recommend to adhere to the following principles also:

.. _best practices:

#. design your applications with restartability in mind.
#. create Data-Structures that are idempotent on multiple loads of the same data.
#. implement continuity-checks if data is continuos.

