First off, thank you for considering contributing to core4. 

There are many ways to contribute, including submitting bug reports, improving 
documentation, submitting feature requests, reviewing new submissions, or 
contributing code that can be incorporated into the project.

> When contributing to this repository, please first discuss the change you 
wish to make via issue, email, or any other method with the owners of this 
repository before making a change.

Please note we have a code of conduct, please follow it in all your 
interactions with the project.

**Table of Contents:**
1. [Code of Conduct](#code-of-conduct)
    1.1. [Our Standards](#our-standards)
    1.2. [Our Responsibilities](#our-responsibilities)
    1.3. [Scope](#scope)
2. [Contributing Code](#contributing-code)
    2.1. [Reporting Bug](#reporting-bug)
    2.2. [Suggesting Enhancements](#suggesting-enhancements)
    2.3. [Pull Request Guidelines](#pull-request-guidelines)
3. [Styleguides](#styleguides)
    3.1. [Git Commit Styleguides](#git-commit-styleguides)
    3.2. [Python Styleguide](#python-styleguid)
    3.3. [Documentation Styleguide](#documentation-styleguide)
4. [APPENDIX](#appendix)
    4.1 [Bug Fix Pull Request Template](#bug-fix-pull-request-template) 
    4.2 [Suggesting Enhancements Pull Request Template](#suggesting-enhancements-pull-request-template) 


## Code of Conduct
### Our Standards
Examples of behavior that contributes to creating a positive environment include:
- Using welcoming and inclusive language.
- Being respectful of differing viewpoints and experiences.
- Gracefully accepting constructive criticism.
- Focusing on what is best for the community.
- Showing empathy towards other community members.

Examples of unacceptable behavior by participants include:
- Trolling, insulting/derogatory comments, and personal or political attacks.
- Public or private harassment.
- Publishing others' private information, such as a physical or electronic 
address, without explicit permission.
- Other conduct which could reasonably be considered inappropriate in a 
professional setting.

### Our Responsibilities
Project maintainers are responsible for clarifying the standards of acceptable 
behavior and are expected to take appropriate and fair corrective action in 
response to any instances of unacceptable behavior.

Project maintainers have the right and responsibility to remove, edit, or 
reject comments, commits, code, wiki edits, issues, and other contributions 
that are not aligned to this Code of Conduct, or to ban temporarily or 
permanently any contributor for other behaviors that they deem inappropriate, 
threatening, offensive, or harmful.

### Scope
This Code of Conduct applies both within project spaces and in public spaces 
when an individual is representing the project or its community. Examples of 
representing a project or community include using an official project e-mail 
address, posting via an official social media account, or acting as an 
appointed representative at an online or offline event. Representation of a 
project may be further defined and clarified by project maintainers.

## Contributing Code
### Reporting Bug
This section guides you through submitting a bug report for core4. Following 
these guidelines helps maintainers and the community understand your report, 
reproduce the behavior, and find related reports.

Before creating bug reports:
- Please check this list (link) as you might find out that you don't need to 
create one.
- Only open an issue if no other issue is addressing the same problem. 
If the bug still persists after the issue has been marked as "fixed", 
please open a new one with a link to the original.
- Try reproducing the bug on a freshly configured machine (not report bugs in 
a customized python environment)

When you are create a bug report, please include as many details as possible. 

How Do I Submit A Bug Report?

Explain the problem and include additional details to help maintainers 
reproduce the problem:
- Use a clear and descriptive title for the issue to identify the problem.
- Describe the exact steps which reproduce the problem in as many details 
as possible.
- Provide specific examples to demonstrate the steps. Include links to files, 
attaching logs or copy/pasteable snippets, which you use in those examples.
- Include configuration/environment information necessary to reproduce.
- Explain which behavior you expected to see.
- Describe the behavior you observed after following the steps and point out 
what exactly is the problem with that behavior.


Use the form below to reporting a bug:
```sh
Title of the issue:

What necessary information needed to reproduce(configuration/environment)?

What steps will reproduce the issue?

What is the expected result?

What happens instead?

```

### Suggesting Enhancements
This section guides you through submitting an enhancement suggestion for core4, 
including completely new features and minor improvements to existing 
functionality. Following these guidelines helps maintainers and the community 
understand your suggestion and find related suggestions.

Before creating enhancement suggestions, please check this list (link) as you 
might find out that you don't need to create one. When you are creating an 
enhancement suggestion, please include as many details as possible.


How Do I Submit A Enhancement Suggestion?
- Use a clear and descriptive title for the enhancement to identify the 
suggestion.
- Provide a step-by-step description of the suggested enhancement in as many 
details as possible.
- Provide specific examples to demonstrate the steps.

Use the form below to submit enhancement suggestion:
```sh
Title of the suggesting enhancement:

Description of the suggested enhancement:

What is the expected result?

```

### Pull Request Guidelines
The process described here has several goals:
- Maintain core4 quality.
- Fix issues that are important to users.
- Engage the community in working toward the best possible core4.
- Enable a sustainable system for core4's maintainers to review contributions.

Please follow these steps to have your contribution considered by the maintainers:
 1. Follow all instructions in the [template](#appendix).
 2. Follow the [styleguides](#styleguides).
 3. Before submiting a pull request:
    - create or extend suitable tests.
    - ensure that all tests run sucecssfully. Further information how to run 
    the tests can be found here: [README](README.md) file.
    - create or update the documentation.
    
>Proof your changes with upstream  code
 
While the prerequisites above must be satisfied prior to having your pull 
request reviewed, the reviewer(s) may ask you to complete additional design 
work, tests, or other changes before your pull request can be 
ultimately accepted.

## Styleguides
### Git Commit Styleguides
Git Commit Messages
- Use the present tense ("Add feature" not "Added feature").
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...").
- The commit message should reference the issue number, e.g. 
("[#18882]:bug: Fix scroll").
- Start a commit message with an applicable title:
    - :**bug**: when fixing a bug.
    - :**new**: when add a enhancements (new features and minor improvements).
    - :**remove**: when removing code or files.
    - :**test**: when adding/editing tests.
    - :**style**: when improving the format/structure of the code.
    - :**doc**: when adding/fixing documentation.

### Python Styleguide
Use [PEP8](https://www.python.org/dev/peps/pep-0008/) style guide. PEP8 is big, 
constantly evolving and certainly worth reading. The main guidelines each core4 
contributor should follow are summarised below:

* Use four whitespaces, no tabulators, with a maximum line length of 79 chars.
* Functions and classes are seperated by two blank lines.
* Methods in a class are seperated by one blank line.
* Put one space around variable assignments (e.g. ``x = 1``) but do not put
  spaces around list indexes, function calls or keyword assignments (e.g.
  ``func(a=1, b=2)``).
* Functions, variables, attributes in lower case using underscore to seperate
  terms.
* Protected attributes with a leading underscore.
* Private attributes with double leading underscore.
* Classes and exceptions use CamelCase.
* Constants use upper case.
* Instance methods use ``self``, class methods use ``cls``.
* Always put import statements at the top of the file.
* Always use absolute imports, avoid using relative imports.
* Imports should be in the following order: standard library modules, third
  party modules, core4 modules.
* Write documentation for every module and introduce the contents of the module 
  and any important classes or functions.
* Write documentation for every class and introduce behavior, important 
  attributes, subclass behavior.
* Write documentation for every non-private functions, list and explain every 
  argument and return value.
  
These guidelines are based on PEP8 and heavily influenced by Brett Slatkin's
Effective Python - 50 Specific Ways to Write Better Python.

Shebang line:
- All core4 modules must not provide a shebang line. For actual scripts located 
in ./scripts the correct shebang line is:
```sh
#!/usr/bin/env python3
```

### Documentation Styleguide
- Use [Sphinx](http://www.sphinx-doc.org) for building the documentation. 
Further information can be found here: [README](README.md).
- Headline hierarchy should be:
```sh   
#######
level 1
#######
    
level 2
=======
    
level 3
-------
```

## APPENDIX
### Bug Fix Pull Request Template

 * Fill out the template below. Any pull request that does not include enough 
 information to be reviewed in a timely manner may be closed at the 
 maintainers' discretion.
 * The pull request must only fix an existing bug. To contribute other changes, 
 you must use a different template.
 * The pull request must update the test suite to demonstrate the changed 
 functionality.
 
```sh   
Identify the Bug
!!! Link to the issue describing the bug that you're fixing. If there is not yet an issue for your bug, please open a new issue and then link to that issue in your pull request.

Bug description:
!!! Provide short bug description

Description of the Change
!!! We must be able to understand the design of your change from this description. If we can't get a good idea of what the code will be doing from the description here, the pull request may be closed at the maintainers' discretion. Keep in mind that the maintainer reviewing this PR may not be familiar with or have worked with the code here recently, so please walk us through the concepts.

Impacted area
!!! Please mention all of the areas that code deals with.

Possible Drawbacks
!!! What are the possible side-effects or negative impacts of the code change?
 ```

### Suggesting Enhancements Pull Request Template

 * Fill out the template below. Any pull request that does not include enough 
 information to be reviewed in a timely manner may be closed at the 
 maintainers' discretion.
 * The pull request must provide only one suggesting enhancement. To contribute 
 other changes, you must use a different template.
 * The pull request must have a test suite to demonstrate the new functionality.

```sh   
Identify the suggested enhancement
!!! Link to the ticket describing the suggested enhancement. If there is not yet a ticket for your suggested enhancement, please create a new ticket and then link to that ticket in your pull request.

Description of the Idea
!!! We must be able to understand the design of your feature from this description. If we can't get a good idea of what the code will be doing from the description here, the pull request may be closed at the maintainers' discretion.

Steps to Demonstrate
!!! Provide specific examples to demonstrate the enhancements.

Impacted area
!!! Please mention all of the areas that code deals with.
 ```
