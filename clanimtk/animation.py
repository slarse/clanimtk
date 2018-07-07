# -*- coding: utf-8 -*-
"""
.. module: animation
    :platform: Unix
    :synopsis: _Animation decorators.
.. moduleauthor:: Simon Larsén <slarse@kth.se>
"""
import itertools
import functools
from clanimtk.util import concatechain, BACKSPACE_GEN, BACKLINE_GEN
from clanimtk.cli import BACKLINE, BACKSPACE


def animation(animation_func):
    """A wrapper for string generators. Provided an endless string generator
    function, Animation will turn it into an animation generator that yields
    frames (endlessly), that contain both the characters the generator
    provides, and escape codes to back up the cursor to the starting position.

    Args:
        animation_func: A function that returns an endles generator.

    Returns:
        an animation decorator function.
    """
    anim = _Animation(animation_func)

    @functools.wraps(animation_func)
    def wrapper(*args, **kwargs):
        return anim(*args, **kwargs)

    return wrapper


class _Animation:
    """A wrapper class for animation generators. It automatically backs up
    the cursor after each frame, and provides reset and erase functionality.

    .. DANGER::

        Do not use directly, use the animation function instead.

    """

    def __init__(self,
                 animation_func,
                 current_generator=None,
                 back_up_generator=None,
                 animation_args=None,
                 animation_kwargs=None):
        self._animation_func = animation_func
        self._current_generator = current_generator
        self._back_up_generator = back_up_generator
        self._animation_args = animation_args
        self._animation_kwargs = animation_kwargs
        self._current_frame = ""

    def reset(self):
        """Reset the current animation generator."""
        animation_gen = self._animation_func(*self._animation_args,
                                             **self._animation_kwargs)
        self._current_generator = itertools.cycle(
            concatechain(animation_gen, self._back_up_generator))

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
            self._animation_func, *args, **kwargs)
        self.reset()
        return cls(self._animation_func, self._current_generator,
                   self._back_up_generator, args, kwargs)

    def __iter__(self):
        return iter(self._current_generator)


def _get_back_up_generator(animation_func, *args, **kwargs):
    """Create a generator for the provided animation function that backs up
    the cursor after a frame. Assumes that the animation function provides
    a generator that yields strings of constant width and height.

    Args:
        animation_func (function): A function that returns an animation generator.
        args (tuple): Arguments for animation_func.
        kwargs (dict): Keyword arguments for animation_func.
    Returns:
        generator: A generator that generates backspace/backline characters for
        the animation func generator.
    """
    lines = next(animation_func(*args, **kwargs)).split('\n')
    width = len(lines[0])
    height = len(lines)
    if height == 1:
        return BACKSPACE_GEN(width)
    return BACKLINE_GEN(height)


def _backspaced_single_line_animation(animation_, *args, **kwargs):
    """Turn an animation into an automatically backspaced animation.

    Args:
        animation (func): A function that returns a generator that yields
        strings for animation frames.
        args (tuple): Arguments for the animation function.
        kwargs (dict): Keyword arguments for the animation function.
    Returns:
        The animation generator, with backspaces applied to each but the first
        frame.
    """
    animation_gen = animation_(*args, **kwargs)
    yield next(animation_gen)  # no backing up on the first frame
    yield from concatechain(BACKSPACE_GEN(kwargs['width']), animation_gen)
