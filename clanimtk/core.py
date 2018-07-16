# -*- coding: utf-8 -*-
"""Core functionality for clanimtk. This module is only intended to be used as
an internal part of clanimtk. The relevant, public functionality in this module
is exposed in the :py:module:: clanimtk.decorator module.

.. module:: core
    :synopsis: Core functionality for clanimtk.
.. moduleauthor:: Simon Larsén <slarse@kth.se>
"""
import asyncio
import functools
import itertools
import sys
from typing import Optional

from clanimtk import util
from clanimtk.cli import BACKLINE, BACKSPACE

ANNOTATED = '_clanimtk_annotated'


class Animate:
    """A wrapper class for adding a CLI animation to a slow-running function.
    Animate uses introspection to figure out if the function it decorates is
    synchronous (defined with 'def') or asynchronous (defined with 'async def'),
    and works with both.

    .. DANGER::

        This class is not intended to be used directly, but rather through the
        animate function.
    """

    def __init__(self, func=None, *, animation_gen, step=.1):
        """Constructor.

        Args:
            func: If Animate is used without kwargs, then the
            function it decorates is passed in here. Otherwise, this is None.
            This argument should NOT be given directly via keyword assignment.
            animation_gen: A generator that yields strings for the animation.
            step: Seconds between each animation frame.
        """
        if not callable(func):
            raise TypeError("argument 'func' for {!r} must be "
                            "callable".format(self.__class__.__name__))
        self._raise_if_annotated(func)
        self._func = func
        self._animation_gen = animation_gen
        self._step = step
        functools.update_wrapper(self, func)

    def __call__(self, *args, **kwargs):
        """Make the class instance callable.

        func (function): If the
        """
        supervisor = util.get_supervisor(self._func)
        return supervisor(self._animation_gen, self._step, *args, **kwargs)

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


class Annotate:
    """A decorator meant for decorating functions that are decorated with the
    animation decorator. It prints a message to stdout before and/or after the
    function has finished.

    .. DANGER::

        This decorator can also be used standalone, but you should NOT decorate a
        function that is decorated with Annotate with Animate. That is to say,
        the decorator order must be like this:

        .. code-block:: python

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


class Animation:
    """A wrapper class for FrameFunctions. It automatically backs up
    the cursor after each frame, and provides reset and erase functionality.

    .. DANGER::

        Do not use directly, use the animation function instead.

    """

    def __init__(self,
                 frame_function,
                 current_generator=None,
                 back_up_generator=None,
                 animation_args=None,
                 animation_kwargs=None):
        self._frame_function = frame_function
        self._current_generator = current_generator
        self._back_up_generator = back_up_generator
        self._animation_args = animation_args
        self._animation_kwargs = animation_kwargs
        self._current_frame = ""

    def reset(self):
        """Reset the current animation generator."""
        animation_gen = self._frame_function(*self._animation_args,
                                             **self._animation_kwargs)
        self._current_generator = itertools.cycle(
            util.concatechain(animation_gen, self._back_up_generator))

    def get_erase_frame(self):
        """Return a frame that completely erases the current frame, and then
        backs up.

        Assumes that the current frame is of constant width."""
        lines = self._current_frame.split('\n')
        width = len(lines[0])
        height = len(lines)
        line = ' ' * width
        if height == 1:
            frame = line + BACKSPACE * width
        else:
            frame = '\n'.join([line] * height) + BACKLINE * (height - 1)
        return frame

    def __next__(self):
        self._current_frame = next(self._current_generator)
        return self._current_frame

    def __call__(self, *args, **kwargs):
        cls = self.__class__
        self._animation_args = args
        self._animation_kwargs = kwargs
        self._back_up_generator = _get_back_up_generator(
            self._frame_function, *args, **kwargs)
        self.reset()
        return cls(self._frame_function, self._current_generator,
                   self._back_up_generator, args, kwargs)

    def __iter__(self):
        return iter(self._current_generator)


def _get_back_up_generator(frame_function, *args, **kwargs):
    """Create a generator for the provided animation function that backs up
    the cursor after a frame. Assumes that the animation function provides
    a generator that yields strings of constant width and height.

    Args:
        frame_function: A function that returns a FrameGenerator.
        args: Arguments for frame_function.
        kwargs: Keyword arguments for frame_function.
    Returns:
        a generator that generates backspace/backline characters for
        the animation func generator.
    """
    lines = next(frame_function(*args, **kwargs)).split('\n')
    width = len(lines[0])
    height = len(lines)
    if height == 1:
        return util.BACKSPACE_GEN(width)
    return util.BACKLINE_GEN(height)


def _backspaced_single_line_animation(animation_, *args, **kwargs):
    """Turn an animation into an automatically backspaced animation.

    Args:
        animation: A function that returns a generator that yields
        strings for animation frames.
        args: Arguments for the animation function.
        kwargs: Keyword arguments for the animation function.
    Returns:
        the animation generator, with backspaces applied to each but the first
        frame.
    """
    animation_gen = animation_(*args, **kwargs)
    yield next(animation_gen)  # no backing up on the first frame
    yield from util.concatechain(
        util.BACKSPACE_GEN(kwargs['width']), animation_gen)
