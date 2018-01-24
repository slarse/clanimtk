"""Unit tests for the cli module.

Author: Simon Larsén
"""
import threading
import time
import asynctest
from asynctest import patch as apatch
from .context import clanimtk
from clanimtk import cli
from clanimtk import util

class CliTest(asynctest.TestCase):

    @apatch('sys.stdout.write')
    async def test_erase(self, mock_write):
        msg = 'This is a message'
        cli.erase(msg)
        mock_write.assert_any_call('\x08'*len(msg))

    @apatch('sys.stdout.write')
    @apatch('sys.stdout.flush')
    async def test_animate_cli(self, mock_flush, mock_write):
        signal = util.Signal()
        animation_mock = asynctest.MagicMock()
        char = '*'
        animation_mock.__next__ = asynctest.MagicMock(return_value=char)
        animation_mock.get_erase_frame = asynctest.MagicMock(return_value='')
        step = .1
        with apatch('time.sleep'):
            thread = threading.Thread(target=cli.animate_cli,
                                      args=(animation_mock, step, signal))
            thread.start()
        # poll to see that the loop has run at least once
        time.sleep(.01)
        signal.done = True
        mock_flush.assert_called()
        animation_mock.__next__.assert_called()
        mock_write.assert_any_call(char)
