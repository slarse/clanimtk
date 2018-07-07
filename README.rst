clanimtk
*******************************************************

`Docs`_

.. image:: https://travis-ci.org/slarse/clanimtk.svg?branch=master
    :target: https://travis-ci.org/slarse/clanimtk
    :alt: Build Status
.. image:: https://codecov.io/gh/slarse/clanimtk/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/slarse/clanimtk
    :alt: Code Coverage
.. image:: https://readthedocs.org/projects/clanimtk/badge/?version=latest
    :target: http://clanimtk.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status
.. image:: https://badge.fury.io/py/clanimtk.svg
    :target: https://badge.fury.io/py/clanimtk
    :alt: PyPi Version
.. image:: https://img.shields.io/badge/python-3.6-blue.svg
    :target: https://badge.fury.io/py/pdfebc
    :alt: Supported Python Versions

.. contents::

Overview
========
``clanimtk`` (Command Line Animation Toolkit) is a toolkit for quickly creating
custom command line animations.

Core concepts
=============
``clanimtk`` works with a few, simple core concepts that revolve around certain
object types. It is essential to have these in the back of the head to
efficiently use the toolkit.

* **``FrameGenerator``:** A ``FrameGenerator`` is any generator that has no
  sendtype nor returntype, and yields any number of strings that have a
  constant width and height. That is to say, each string must have fixed line
  lengths, and no string may differ in dimensions from any other.
* **``FrameFunction``:** Any function that returns a ``FrameGenerator``.
* **``AnimationGenerator``:** A generator that yields an endless amount of strings,
  where each string is terminated with characters that back up the cursor to its
  starting point (after the string has been printed).
* **``Animation``:** Any function that returns an ```AnimationGenerator``.

Knowing about these concepts, we can turn to the main functionality of
``clanimtk``, which is provided in the form of two decorators.

* **``@animation``:** Turns a ``FrameFunction`` into an ``Animation``.
* **``@animate``:** Given an ``AnimationGenerator``, ``@animate`` will print
  frames to stdout as long as the decorated function is running.

Using ``clanimtk``, the only thing you need to write yourself to create a
custom animation is a ``FrameFunction``. Decorating a ``FrameFunction``
with the ``@animation`` decorator will transform the function into an
``Animation``. Below is a minimal example with the default animation
of ``clanimtk``.

.. code-block:: python
    
    from clanimtk import animation

    @animation
    def hashes():
        return (("#" * i).ljust(4) for i in range(5))

The function returns a generator which yields the strings ``"    "``, ``"#
"``, ``"## "``, ``"### "`` and ``"####"``. Each has one line and is 4
characters wide, so by definition the generator is a ``FrameGenerator``, making
the function a ``FrameFunction``. Applying the ``@animation`` decorator
transforms it into an ``Animation``. The ``AnimationGenerator`` it returns
can be used with the ``@animate`` decorator:

.. code-block:: python

    from clanimtk import animate
    import time

    @animate(animation=hashes())
    def sleep(duration):
        time.sleep(duration)
        return 42
        
You can see the not-too-impressive results in the gif below.

.. image:: images/example_animation.gif
    :alt: An example animation

However, with some effort and perseverance, it's possible to create some pretty
cool animations:

.. image:: images/hello_world.gif
    :alt: Scrolling text animation

Some more examples, including the scrolling text animation seen above, can be
found in the ``clanim`` package.

Requirements
============
* For production use, only `daiquiri` is required (for logging).
* For development, see `requirements.txt`_.

Install
=======
Option 1: Install from PyPi with ``pip``
----------------------------------------
The latest release of ``clanimtk`` is on PyPi, and can thus be installed as usual with ``pip``.
I strongly discourage system-wide ``pip`` installs (i.e. ``sudo pip install <package>``), as this
may land you with incompatible packages in a very short amount of time. A per-user install
can be done like this:

1. Execute ``pip install --user clanimtk`` to install the package.
2. Further steps to be added ...

Option 2: Clone the repo and the install with ``pip``
-----------------------------------------------------
If you want the dev version, you will need to clone the repo, as only release versions are uploaded
to PyPi. Unless you are planning to work on this yourself, I suggest going with the release version.

1. Clone the repo with ``git``:
    - ``git clone https://github.com/slarse/clanimtk``
2. ``cd`` into the project root directory and install with ``pip``.
    - ``pip install --user .``, this will create a local install for the current user.
    - Or just ``pip install .`` if you use ``virtualenv``.
    - For development, use ``pip install -e .`` in a ``virtualenv``.
3. Further steps to be added ...
   
License
=======
This software is licensed under the MIT License. See the `license file`_ file for specifics.

Contributing
============
To be added ...

.. _license file: LICENSE
.. _sample configuration: config.cnf
.. _requirements.txt: requirements.txt
.. _Docs: https://clanimtk.readthedocs.io/en/latest/
