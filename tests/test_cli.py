"""Unit tests for the cli module.

Author: Simon Larsén
"""
import threading
import time
from multiprocessing import Event
from unittest.mock import MagicMock, patch
import pytest
from clanimtk import cli
from clanimtk import util


@pytest.fixture()
def mock_write(mocker):
    return mocker.patch('sys.stdout.write')


@pytest.fixture()
def mock_flush(mocker):
    return mocker.patch('sys.stdout.flush')


def test_erase(mock_write):
    msg = 'This is a message'
    cli.erase(msg)
    mock_write.assert_any_call('\x08' * len(msg))


def test_animate_cli(mock_flush, mock_write):
    event = Event()
    animation_mock = MagicMock()
    char = '*'
    animation_mock.__next__ = MagicMock(return_value=char)
    animation_mock.get_erase_frame = MagicMock(return_value='')
    step = .1
    with patch('time.sleep'):
        thread = threading.Thread(
            target=cli.animate_cli, args=(animation_mock, step, event))
        thread.start()
    time.sleep(.01)
    event.set()  # terminate

    animation_mock.__next__.assert_called()
