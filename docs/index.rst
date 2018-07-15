.. clanimtk documentation master file, created by
   sphinx-quickstart on Thu Jun 29 18:11:20 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to clanimtk's documentation!
==================================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:
    code

Core concepts
=============
``clanimtk`` works with a few, simple core concepts that revolve around certain
object types. It is beneficial to keep these in the back of the head when
using the toolkit.

* **Frame:** A string with fixed linelength. I.e., Either there is only
  one line in the string, or each newline character is preceeded by the exact
  same amount of characters.
* **FrameGenerator:** A ``FrameGenerator`` is any generator that has no
  sendtype nor returntype, and yields any number of ``Frame`` strings that
  have identical dimensions. That is to say, each ``Frame`` yielded by
  the generator must have the same amount of lines, and same linelength,
  as all of the others.
* **FrameFunction:** Any function that returns a ``FrameGenerator``.
* **AnimationGenerator:** A generator that yields an endless amount of
  ``Frame`` strings, but each ``Frame`` is terminated by backspace/up
  character such that printing the ``Frame`` results in the cursor ending
  up at its start position.
* **Animation:** Any function that returns an ``AnimationGenerator``.

All of these types, along with some other types used in the package, are
type-defined in the `types module`_. Do note that several of the types
are simply aliases of each other, or other existing types.

Knowing about these concepts, we can turn to the main functionality of
``clanimtk``, which is provided in the form of two decorators.

* **@animation:** Turns a ``FrameFunction`` into an ``Animation``.
* **@animate:** Given an ``AnimationGenerator``, ``@animate`` will print
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

    @animate(animation=hashes()) # note that the Animation is called to produce an AnimationGenerator
    def sleep(duration):
        time.sleep(duration)
        return 42
        
You can see the not-too-impressive results in the gif below.

.. image:: images/example_animation.gif
    :alt: An example animation

Creating a multiline animation is similarly simple, you simply create ``Frame``
strings that each have the same number of lines.

.. code-block:: python
    
    import time
    from clanimtk import animation, animate

    # note that there is invisible whitespace to the right
    # of some characters. For example, the first line in the
    # A actually looks like `_XXX_`, where `_` is a space.
    a = """
     XXX 
    X   X
    XXXXX
    X   X
    X   X""".strip('\n')

    b = """
    XXXX 
    X   X
    XXXX 
    X   X
    XXXX """.strip('\n')
    
    @animation
    def ab():
        return iter([a, b])

    @animate(animation=ab(), step=.5) # step is approx seconds between frames
    def func():
        time.sleep(10)

This ends up looking like this:

.. image:: images/ab.gif
    :alt: Simple multiline animation

For more examples, have a look at the ``clanim`` package!


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
