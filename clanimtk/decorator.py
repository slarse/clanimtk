# -*- coding: utf-8 -*-
"""
.. module:: decorator
    :platform: Unix
    :synopsis: This module contains all of the clanim decorators.
.. moduleauthor:: Simon Larsén <slarse@kth.se>
"""
#pylint: disable=missing-docstring,too-few-public-methods
import asyncio
import logging
import functools
import sys
import itertools
import daiquiri
from clanimtk.util import get_supervisor
from clanimtk.animation import Animation

daiquiri.setup(level=logging.ERROR)
LOGGER = daiquiri.getLogger(__name__)

ANNOTATED = '_clanimtk_annotated'
ASYNC_ANIMATED = '_clanimtk_asnyc_animated'

@Animation
def _default_animation():
    return itertools.cycle([("#"*i).ljust(5) for i in range(5)])

class Annotate:
    """A decorator meant for decorating functions that are decorated with the
    Animation decorator. It prints a message to stdout before and/or after the
    function has finished.

    This decorator can also be used standalone, but you should NOT decorate a
    function that is decorated with Annotate with Animate. That is to say,
    the decorator order must be like this:

        @Annotate
        @Animate
        def some_function()
            pass
    """
    def __init__(self, *,start_msg=None, end_msg=None, start_no_nl=False):
        """Note that both arguments are keyword only arguments.

        Args:
            start_msg (str): A message to print before the function runs.
            end_msg (str): A message to print after the function has finished.
            start_no_nl (bool): If True, no newline is appended after the
            start_msg.
        """
        if start_msg is None and end_msg is None:
            raise ValueError(
                "At least one of 'start_msg' and 'end_msg' must be specified.")
        self._raise_if_not_none_nor_string(start_msg, "start_msg")
        self._raise_if_not_none_nor_string(end_msg, "end_msg")
        self._start_msg = start_msg
        self._end_msg = end_msg
        self._start_no_nl = start_no_nl

    def _raise_if_not_none_nor_string(self, msg, parameter_name):
        if msg is not None and not isinstance(msg, str):
            raise TypeError(
                f"Bad operand type for {self.__class__.__name__!r}"
                f".{parameter_name}: {type(msg)}")

    def _start_print(self):
        """Print the start message with or without newline depending on the
        self._start_no_nl variable.
        """
        if self._start_no_nl:
            sys.stdout.write(self._start_msg)
            sys.stdout.flush()
        else:
            print(self._start_msg)

    def __call__(self, func, *args, **kwargs):
        """
        Args:
            func (function): The annotated function.
            args (tuple): Arguments for func.
            kwargs (dict): Keyword arguments for func.
        """
        if asyncio.iscoroutinefunction(func):
            return self._async_call(func, *args, **kwargs)
        return self._sync_call(func, *args, **kwargs)

    def _sync_call(self, func):
        """__call__ function for regular synchronous functions.

        Args:
            func (function): The annotated function.
            args (tuple): Arguments for func.
            kwargs (dict): Keyword arguments for func.
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if self._start_msg:
                self._start_print()
            result = func(*args, **kwargs)
            if self._end_msg:
                print(self._end_msg)
            return result
        setattr(wrapper, ANNOTATED, True)
        return wrapper

    def _async_call(self, func):
        """__call__ function for asyncio coroutines.

        Args:
            func (function): The annotated function.
            args (tuple): Arguments for func.
            kwargs (dict): Keyword arguments for func.
        """
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            if self._start_msg:
                print(self._start_msg)
            result = await func(*args, **kwargs)
            if self._end_msg:
                print(self._end_msg)
            return result
        setattr(wrapper, ANNOTATED, True)
        return wrapper

def animate(func=None, *, animation=_default_animation(), step=0.1):
    if callable(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return _Animate(func=func, animation=animation, step=step)(*args, **kwargs)
        ret = wrapper
    elif func is None:
        def outer(f):
            @functools.wraps(f)
            def inner(*args, **kwargs):
                return _Animate(func=f, animation=animation, step=step)(*args, **kwargs)
            return inner
        ret = outer
    else:
        raise TypeError("argument 'func' must either be None or callable")
    # maintain corutinefunction status, if present
    return ret if not asyncio.iscoroutinefunction(func)\
               else asyncio.coroutine(ret)


class _Animate:
    """A wrapper class for adding a CLI animation to a slow-running function.
    Animate uses introspection to figure out if the function it decorates is
    synchronous (defined with 'def') or asynchronous (defined with 'async def'),
    and works with both.

    .. DANGER::

        This class is not intended to be used directly, but rather through the
        animate function.
    """

    def __init__(self, func=None, *, animation=_default_animation(), step=.1):
        """Constructor.

        Args:
            func (function): If Animate is used without kwargs, then the
            function it decorates is passed in here. Otherwise, this is None.
            This argument should NOT be given directly.
            animation (generator): A generator that yields strings for the animation.
            step (float): Seconds between each animation frame.
        """
        if not callable(func):
            raise TypeError("argument 'func' for {!r} must be "
                            "callable".format(self.__class__.__name__))
        if asyncio.iscoroutinefunction(func):
            setattr(self, ASYNC_ANIMATED, True)
        self._raise_if_annotated(func)
        self._func = func
        self._animation = animation
        self._step = step
        functools.update_wrapper(self, func)

    def _call_without_kwargs(self, animation_, step, func, *args, **kwargs):
        """The function that __call__ calls if the constructor did not recieve
        any kwargs.

        NOTE: This method should ONLY be called directly in the constructor!

        Args:
            animation_ (generator): A generator yielding strings for the animation.
            step (float): Seconds between each animation frame.
            func (function): A function to run alongside an animation.
            args (tuple): Positional arguments for func.
            kwargs (dict): Keyword arguments for func.
        Returns:
            A function if func is a function, and a coroutine if func is a
            coroutine.
        """
        return get_supervisor(func)(animation_, step, *args, **kwargs)

    def __call__(self, *args, **kwargs):
        """Make the class instance callable.

        func (function): If the
        """
        supervisor = get_supervisor(self._func)
        return supervisor(self._animation, self._step, *args, **kwargs)

    def _raise_if_annotated(self, func):
        """Raise TypeError if a function is decorated with Annotate, as such
        functions cause visual bugs when decorated with Animate.

        Animate should be wrapped by Annotate instead.

        Args:
            func (function): Any callable.
        Raises:
            TypeError
        """
        if hasattr(func, ANNOTATED) and getattr(func, ANNOTATED):
            msg = ('Functions decorated with {!r} '
                   'should not be decorated with {!r}.\n'
                   'Please reverse the order of the decorators!'
                   .format(self.__class__.__name__, Annotate.__name__))
            raise TypeError(msg)
