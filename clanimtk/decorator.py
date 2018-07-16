# -*- coding: utf-8 -*-
"""
.. module:: decorator
    :synopsis: This module contains all of the clanim decorators and essentially constitutes the public API of the package.
.. moduleauthor:: Simon Larsén <slarse@kth.se>
"""
#pylint: disable=missing-docstring,too-few-public-methods
import asyncio
import functools
import sys
from typing import Optional

from clanimtk import types
from clanimtk import core
from clanimtk.util import get_supervisor, concatechain


def animation(frame_function: types.FrameFunction) -> types.Animation:
    """Turn a FrameFunction into an Animation.

    Args:
        frame_function: A function that returns a FrameGenerator.

    Returns:
        an Animation decorator function.
    """
    animation_ = core.Animation(frame_function)

    @functools.wraps(frame_function)
    def wrapper(*args, **kwargs):
        return animation_(*args, **kwargs)

    return wrapper


@animation
def _default_animation():
    return (("#" * i).ljust(4) for i in range(5))


def animate(func: types.AnyFunction = None,
            *,
            animation: types.AnimationGenerator = _default_animation(),
            step: float = 0.1) -> types.AnyFunction:
    """Wrapper function for the _Animate wrapper class.
    
    Args:
        func: A function to run while animation is showing.
        animation: An AnimationGenerator that yields animation frames.
        step: Approximate timestep (in seconds) between frames.
    Returns:
        An animated version of func if func is not None. Otherwise, a function
        that takes a function and returns an animated version of that.
    """
    if callable(func):
        return _animate_no_kwargs(func, animation, step)
    elif func is None:
        return _animate_with_kwargs(animation_gen=animation, step=step)
    else:
        raise TypeError("argument 'func' must either be None or callable")


def _animate_no_kwargs(func, animation_gen, step):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return core.Animate(
            func=func, animation_gen=animation_gen, step=step)(*args, **kwargs)
    return wrapper if not asyncio.iscoroutinefunction(func)\
                   else asyncio.coroutine(wrapper)


def _animate_with_kwargs(*, animation_gen, **decorator_kwargs):
    def outer(func):
        @functools.wraps(func)
        def inner(*args, **function_kwargs):
            return core.Animate(func=func, animation_gen=animation_gen, **decorator_kwargs)\
                   (*args, **function_kwargs)
        return inner if not asyncio.iscoroutinefunction(func)\
                       else asyncio.coroutine(inner)

    return outer


def annotate(*,
             start_msg: Optional[str] = None,
             end_msg: Optional[str] = None,
             start_no_nl: bool = False) -> types.AnyFunction:
    """A decorator meant for decorating functions that are decorated with the
    `animate` decorator. It prints a message to stdout before and/or after the
    function has finished.

    .. DANGER::

        This decorator can also be used standalone, but you should NOT decorate a
        function that is decorated with `annotate` with `animate`. That is to say,
        the decorator order must be like this:

        .. code-block:: python

            @annotate
            @animate
            def some_function()
                pass
    """
    return core.Annotate(start_msg=start_msg, end_msg=end_msg, start_no_nl=start_no_nl)


def multiline_frame_function(frame_function: types.FrameFunction,
                             height: int,
                             offset: int = 0,
                             *args,
                             **kwargs) -> types.FrameGenerator:
    """Multiline a singlelined frame function. Simply chains several frame
    generators together, and applies the specified offset to each one.

    Args:
        frame_function: A function that returns a singleline FrameGenerator.
        height: The amount of frame generators to stack vertically (determines
        the height in characters).
        offset: An offset to apply to each successive generator. If the offset
        is 2, then the first generator starts at frame 0, the second at frame
        2, the third at frame 4, and so on.

    Returns:
        a multiline version fo the generator returned by frame_function
    """
    frame_generators = []
    for i in range(height):
        frame_generators.append(frame_function(*args, **kwargs))
        for _ in range(i * offset):  # advance animation
            frame_generators[i].__next__()
    frame_gen = concatechain(*frame_generators, separator='\n')
    yield from frame_gen
