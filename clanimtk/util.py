# -*- coding: utf-8 -*-
# pylint: disable=too-few-public-methods
"""
.. module:: util
    :synopsis: This module contains utility functions.
.. moduleauthor:: Simon Larsén <slarse@kth.se>
"""

import asyncio
import functools
import itertools
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Event

from clanimtk import types
from clanimtk.cli import animate_cli, BACKSPACE

BACKSPACE_GEN = lambda size: itertools.cycle([BACKSPACE * size])
BACKLINE_GEN = lambda lines: itertools.cycle(['\033[F' * (lines - 1)])


def get_supervisor(func: types.AnyFunction) -> types.Supervisor:
    """Get the appropriate supervisor to use and pre-apply the function.

    Args:
        func: A function.
    """
    if not callable(func):
        raise TypeError("func is not callable")
    if asyncio.iscoroutinefunction(func):
        supervisor = _async_supervisor
    else:
        supervisor = _sync_supervisor
    return functools.partial(supervisor, func)


@contextmanager
def _terminating_event():
    """A contextmanager that yields an Event object, which is always set
    (Event.set()) when the context exits, regardless of how it exits.
    """
    event = Event()
    try:
        yield event
    except:
        raise
    finally:
        event.set()


async def _async_supervisor(func, animation_, step, *args, **kwargs):
    """Supervisor for running an animation with an asynchronous function.

    Args:
        func: A function to be run alongside an animation.
        animation_: An infinite generator that produces
        strings for the animation.
        step: Seconds between each animation frame.
        *args: Arguments for func.
        **kwargs: Keyword arguments for func.
    Returns:
        The result of func(*args, **kwargs)
    Raises:
        Any exception that is thrown when executing func.
    """
    with ThreadPoolExecutor(max_workers=2) as pool:
        with _terminating_event() as event:
            pool.submit(animate_cli, animation_, step, event)
            result = await func(*args, **kwargs)
    return result


def _sync_supervisor(func, animation_, step, *args, **kwargs):
    """Supervisor for running an animation with a synchronous function.

    Args:
        func: A function to be run alongside an animation.
        animation_: An infinite generator that produces
        strings for the animation.
        step: Seconds between each animation frame.
        args: Arguments for func.
        kwargs: Keyword arguments for func.
    Returns:
        The result of func(*args, **kwargs)
    """
    with ThreadPoolExecutor(max_workers=1) as pool:
        with _terminating_event() as event:
            pool.submit(animate_cli, animation_, step, event)
            result = func(*args, **kwargs)
    return result


def concatechain(*generators: types.FrameGenerator, separator: str = ''):
    """Return a generator that in each iteration takes one value from each of the
    supplied generators, joins them together with the specified separator and
    yields the result. Stops as soon as any iterator raises StopIteration and
    returns the value contained in it.

    Primarily created for chaining string generators, hence the name.

    Args:
        generators: Any number of generators that yield types that can be
        joined together with the separator string.
        separator: A separator to insert between each value yielded by
        the different generators.
    Returns:
        A generator that yields strings that are the concatenation of one value
        from each of the generators, joined together with the separator string.
    """
    while True:
        try:
            next_ = [next(gen) for gen in generators]
            yield separator.join(next_)
        except StopIteration as exc:
            return exc.value
