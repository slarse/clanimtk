# -*- coding: utf-8 -*-
# pylint: disable=too-few-public-methods
"""
.. module:: util
    :platform: Unix
    :synopsis: This module contains util functions and classes.
.. moduleauthor:: Simon Larsén <slarse@kth.se>
"""
import asyncio
import time
import functools
import itertools
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Event
from clanimtk.cli import animate_cli, BACKSPACE

BACKSPACE_GEN = lambda size: itertools.cycle([BACKSPACE * size])
BACKLINE_GEN = lambda lines: itertools.cycle(['\033[F' * (lines - 1)])


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


def get_supervisor(func):
    """Get the appropriate supervisor to use and pre-apply the function.

    Args:
        func (function): A function.
    """
    if not callable(func):
        raise TypeError("func is not callable")
    if asyncio.iscoroutinefunction(func):
        supervisor = _async_supervisor
    else:
        supervisor = _sync_supervisor
    return functools.partial(supervisor, func)


async def _async_supervisor(func, animation_, step, *args, **kwargs):
    """Supervisor for running an animation with an asynchronous function.

    Args:
        func (function): A function to be run alongside an animation.
        animation_ (generator): An infinite generator that produces
        strings for the animation.
        step (float): Seconds between each animation frame.
        *args (tuple): Arguments for func.
        **kwargs (dict): Keyword arguments for func.
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
        func (function): A function to be run alongside an animation.
        animation_ (generator): An infinite generator that produces
        strings for the animation.
        step (float): Seconds between each animation frame.
        args (tuple): Arguments for func.
        kwargs (dict): Keyword arguments for func.
    Returns:
        The result of func(*args, **kwargs)
    Raises:
        Any exception that is thrown when executing func.
    """
    with ThreadPoolExecutor(max_workers=1) as pool:
        with _terminating_event() as event:
            pool.submit(animate_cli, animation_, step, event)
            result = func(*args, **kwargs)
    return result


def concatechain(*generators, separator=''):
    """Create generator that in each iteration takes one value from each of the
    supplied generators, joins them together with the specified separator and
    yields the result. Stops as soon as any iterator raises StopIteration and
    returns the value contained in it.

    Primarily created for concatenating strings, hence the name.

    Args:
        generators (List[generator]): A list
        separator (str): A separator to insert between each value yielded by
        the different generators.
    Returns:
        A generator as described above.
    """
    while True:
        try:
            next_ = [next(gen) for gen in generators]
            yield separator.join(next_)
        except StopIteration as e:
            return e.value
