
best practices
==============

Use PEP8 style guide. PEP8 is big, constantly evolving and certainly worth 
reading. The main guidelines each core4 contributor should follow are 
summarised below:

* use four whitespaces, no tabulators, with a maximum line length of 79 chars
* functions and classes are seperated by two blank lines
* methods in a class are seperated by one blank line
* put one space around variable assignments (e.g. ``x = 1``) but do not put
  spaces around list indexes, function calls or keyword assignments (e.g.
  ``func(a=1, b=2)``)
* functions, variables, attributes in lower case using underscore to seperate
  terms
* protected attributes with a leading underscore
* private attributes with double leading underscore
* classes and exceptions use CamelCase
* constants use upper case
* instance methods use ``self``, class methods use ``cls``
* always put import statements at the top of the file
* always use absolute imports, avoid using relative imports
* imports should be in the following order: standard library modules, third
  party modules, core4 modules
* write documentation for every module and introduce the contents of the module 
  and any important classes or functions
* write documentation for every class and introduce behavior, important 
  attributes, subclass behavior
* write documentation for every non-private functions, list and explain every 
  argument, return value

These guidelines are based on PEP8 and heavily influenced by Brett Slatkin's
Effective Python - 50 Specific Ways to Write Better Python.


parameters, arguments and interface definitions
-----------------------------------------------

* optional arguments should be placed in square brackets, i.e. ``[PARAMETER]``
* mandatory arguments should be placed in angle brackets, i.e. ``<PARAMETER>``


encoding declarations
---------------------

all core4 files use UTF-8 encoding and must not provide a encoding declaration
in the first or second line of the Python file.


shebang line
------------

all core4 modules must not provide a shebang line. For actual scripts located
in ./scripts the correct shebang line is::

    #!/usr/bin/env python3


sphinx documentation
--------------------

headline hierarchy should be::
    
    #######
    level 1
    #######
    
    level 2
    =======
    
    level 3
    -------
