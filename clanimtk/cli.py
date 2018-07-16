# -*- coding: utf-8 -*-
"""
.. module:: cli
    :synopsis: This module contains all functions that interact with the CLI.
.. moduleauthor:: Simon Larsén <slarse@kth.se>
"""
import sys
import time

BACKSPACE = '\x08'
BACKLINE = '\033[F'


def erase(status):
    """Erases the given status message from stdout by backspacing as many times
    as the status is long.

    Args:
        status (str): A status message that is already printed to stdout.
    """
    sys.stdout.write('\x08' * len(status))


def animate_cli(animation_, step, event):
    """Print out the animation cycle to stdout. This function is for use with
    synchronous functions and must be run in a thread.

    Args:
        animation_ (generator): A generator that produces strings for the
        animation. Should be endless.
        step (float): Seconds between each animation frame.
    """
    while True:  # run at least once, important for tests!
        time.sleep(step)
        frame = next(animation_)
        sys.stdout.write(frame)
        sys.stdout.flush()
        if event.is_set():
            break
    sys.stdout.write(animation_.get_erase_frame())
    sys.stdout.flush()
    animation_.reset()
