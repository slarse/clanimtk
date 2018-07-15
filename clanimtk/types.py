"""A module with type hint aliases.

.. module:: types
    :synopsis: Type hint aliases to reduce clutter in the API.
.. moduleauthor:: Simon Larsén <slarse@kth.se>
"""
from typing import Callable, Generator, Any

AnyFunction = Callable[..., Any]

Frame = str
FrameGenerator = Generator[Frame, None, None]
FrameFunction = Callable[..., FrameGenerator]
AnimationGenerator = Generator[Frame, None, None]
Animation = Callable[..., AnimationGenerator]
Supervisor = Callable[[FrameGenerator, float, Any, Any], Any]
