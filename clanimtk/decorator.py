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
from typing import Generator, Callable, Optional, Any

from clanimtk import types
from clanimtk.util import get_supervisor, concatechain
from clanimtk.animation import animation

ANNOTATED = '_clanimtk_annotated'


@animation
def _default_animation():
    return itertools.cycle([("#" * i).ljust(5) for i in range(5)])


class Annotate:
    """A decorator meant for decorating functions that are decorated with the
    animation decorator. It prints a message to stdout before and/or after the
    function has finished.

    .. DANGER::

        This decorator can also be used standalone, but you should NOT decorate a
        function that is decorated with Annotate with Animate. That is to say,
        the decorator order must be like this:

            @Annotate
            @Animate
            def some_function()
                pass
    """

    def __init__(self,
                 *,
                 start_msg: Optional[str] = None,
                 end_msg: Optional[str] = None,
                 start_no_nl: bool = False):
        """Note that both arguments are keyword only arguments.

        Args:
            start_msg: A message to print before the function runs.  end_msg: A
            message to print after the function has finished.  start_no_nl: If
            True, no newline is appended after the start_msg.
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
            raise TypeError(f"Bad operand type for {self.__class__.__name__!r}"
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
            func: The annotated function.
            args: Arguments for func.
            kwargs: Keyword arguments for func.
        """
        if asyncio.iscoroutinefunction(func):
            return self._async_call(func, *args, **kwargs)
        return self._sync_call(func, *args, **kwargs)

    def _sync_call(self, func):
        """__call__ function for regular synchronous functions.

        Args:
            func: The annotated function.
            args: Arguments for func.
            kwargs: Keyword arguments for func.
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
            func: The annotated function.
            args: Arguments for func.
            kwargs: Keyword arguments for func.
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


def animate(func: Optional[Callable[..., Any]] = None,
            *,
            animation: types.FrameGenerator = _default_animation(),
            step: float = 0.1):
    """Wrapper function for the _Animate wrapper class.
    
    Args:
        func: A function to be animated.
        animation: A generator that yields animation frames.
        step: Approximate timestep between frames.
    Returns:
        An animated version of func if func is not None. Otherwise, a function
        that takes a function and returns an animated version of that.
    """
    if callable(func):
        return _animate_no_kwargs(func, animation, step)
    elif func is None:
        return _animate_with_kwargs(animation=animation, step=step)
    else:
        raise TypeError("argument 'func' must either be None or callable")


def _animate_no_kwargs(func, animation, step):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return _Animate(
            func=func, animation=animation, step=step)(*args, **kwargs)
    return wrapper if not asyncio.iscoroutinefunction(func)\
                   else asyncio.coroutine(wrapper)


def _animate_with_kwargs(**decorator_kwargs):
    def outer(func):
        @functools.wraps(func)
        def inner(*args, **function_kwargs):
            return _Animate(func=func, **decorator_kwargs)\
                   (*args, **function_kwargs)
        return inner if not asyncio.iscoroutinefunction(func)\
                       else asyncio.coroutine(inner)

    return outer


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
            func: If Animate is used without kwargs, then the
            function it decorates is passed in here. Otherwise, this is None.
            This argument should NOT be given directly via keyword assignment.
            animation: A generator that yields strings for the animation.
            step: Seconds between each animation frame.
        """
        if not callable(func):
            raise TypeError("argument 'func' for {!r} must be "
                            "callable".format(self.__class__.__name__))
        self._raise_if_annotated(func)
        self._func = func
        self._animation = animation
        self._step = step
        functools.update_wrapper(self, func)

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
                   'Please reverse the order of the decorators!'.format(
                       self.__class__.__name__, Annotate.__name__))
            raise TypeError(msg)


def multi_line_frame_generator(frame_function: types.FrameFunction,
                               height: int,
                               offset: int = 0,
                               *args,
                               **kwargs) -> types.FrameFunction:
    """Multiline a single-lined frame generator. Simply chains several frame
    generators together, and applies the specified offset to each one.

    Args:
        frame_function: A function that returns a singleline FrameGenerator.
        height: The amount of frame generators to stack vertically (determines
        the height in characters).
        offset: An offset to apply to each successive generator. If the offset
        is 2, then the first generator starts at frame 0, the second at frame
        2, the third at frame 4, and so on.

    Returns:
        A function that returns multiline versions of the provided frame
        generator function.
    """
    frame_generators = []
    for i in range(height):
        frame_generators.append(frame_function(*args, **kwargs))
        for _ in range(i * offset):  # advance animation
            frame_generators[i].__next__()
    frame_gen = concatechain(*frame_generators, separator='\n')
    yield from frame_gen
