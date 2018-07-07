# -*- coding: utf-8 -*-
# pylint: disable=protected-access
# pylint: disable=invalid-name
# pylint: disable=missing-docstring
# pylint: disable=wrong-import-order
"""unit tests for the decorator module.

Author: Simon Larsén
"""
import unittest
import asyncio
import io
import pytest
from inspect import signature
from unittest.mock import MagicMock, Mock, patch
from .context import clanimtk
from clanimtk.decorator import animate, ANNOTATED, _default_animation
from clanimtk import annotate


def animate_test_variables():
    """Return the variables for the animate tests."""
    return_value = 42**42
    mock_function = MagicMock(return_value=return_value)
    setattr(mock_function, ANNOTATED, False)
    docstring = 'This is a test docstring'
    mock_function.__doc__ = docstring
    mock_animation = MagicMock()
    step = .1
    animate_ = animate(animation=mock_animation, step=step)
    return mock_function, return_value, docstring, mock_animation, step, animate_



class TestAnimate:
    def test_animate_with_kwargs_does_not_remove_coroutinefunc_status(self):
        async def func():
            pass

        animated_func = animate(animation=_default_animation())(func)
        assert asyncio.iscoroutinefunction(animated_func)

    def test_animate_with_kwargs_does_not_add_corotuinefunc_status(self):
        def func():
            pass

        animated_func = animate(animation=_default_animation())(func)
        assert not asyncio.iscoroutinefunction(animated_func)

    def test_animate_does_not_remove_corutinefunc_status(self):
        async def func():
            pass

        animated_func = animate(func)
        assert asyncio.iscoroutinefunction(animated_func)

    def test_animate_does_not_add_corotuinefunc_status(self):
        def func():
            pass

        animated_func = animate(func)
        assert not asyncio.iscoroutinefunction(animated_func)

    def test_animate_does_not_modify_signature(self):
        def func(a, b, c):
            pass

        expected_params = signature(func).parameters.keys()
        animated_func = animate(func)
        actual_params = signature(func).parameters.keys()
        assert actual_params == expected_params

    def test_animate_with_non_callable(self):
        non_callable = 1
        with pytest.raises(TypeError):
            animate(func=non_callable)

    @patch('clanimtk.decorator.get_supervisor', side_effect=lambda func: func)
    def test_animate_with_decorator_kwargs(self, mock_get_supervisor):
        """This test emulates using kwargs in the decorator, so
        that the decorator is actually called on the kwargs, and
        not on the function that animate decorates.
        """
        mock_function, return_value, docstring, mock_animation, step, animate_ = (
            animate_test_variables())
        wrapped_function = animate_(mock_function)
        result = wrapped_function()
        mock_get_supervisor.assert_called_once_with(mock_function)
        mock_function.assert_called_once_with(mock_animation, step)
        assert wrapped_function.__doc__ == docstring
        assert result == return_value

    @patch('clanimtk.decorator.get_supervisor', side_effect=lambda func: func)
    def test_animate_with_decorator_kwargs_and_function_args_and_kwargs(
            self, mock_get_supervisor):
        args = ('herro', 2, lambda x: 2 * x)
        kwargs = {'herro': 2, 'python': 42}
        mock_function, return_value, docstring, mock_animation, step, animate_ = (
            animate_test_variables())
        wrapped_function = animate_(mock_function)
        result = wrapped_function(*args, **kwargs)
        mock_get_supervisor.assert_called_once_with(mock_function)
        mock_function.assert_called_once_with(mock_animation, step, *args,
                                              **kwargs)
        assert wrapped_function.__doc__ == docstring
        assert result == return_value

    @patch('clanimtk.decorator.get_supervisor', side_effect=lambda func: func)
    def test_animate_without_decorator_kwargs(self, mock_get_supervisor):
        """Emulates decorating a function without calling the decorator explicitly."""
        mock_function, return_value, docstring, _, _, _ = (
            animate_test_variables())
        wrapped_function = animate(mock_function)
        result = wrapped_function()
        mock_get_supervisor.assert_called_once_with(mock_function)
        mock_function.assert_called_once()
        assert wrapped_function.__doc__ == docstring
        assert result == return_value

    @patch('clanimtk.decorator.get_supervisor', side_effect=lambda func: func)
    def test_animate_without_decorator_kwargs_with_function_args_and_kwargs(
            self, mock_get_supervisor):
        args = ('herro', 2, lambda x: 2 * x)
        kwargs = {'herro': 2, 'python': 42}
        mock_function, return_value, docstring, _, _, _ = (
            animate_test_variables())
        wrapped_function = animate(mock_function)
        result = wrapped_function(*args, **kwargs)
        mock_get_supervisor.assert_called_once_with(mock_function)
        mock_function.assert_called_once()
        assert wrapped_function.__doc__ == docstring
        assert result == return_value


class TestAnnotate:
    def setup(self):
        self.doc = "This is just a stupid test function"

        def func(abra, ka, dabra):
            pass

        func.__doc__ = self.doc
        self.func = func

    def test_annotate_raises_when_start_and_end_msgs_are_none(self):
        with pytest.raises(ValueError):
            annotate()

    def test_annotate_raises_when_start_is_not_none_nor_string(self):
        with pytest.raises(TypeError):
            annotate(start_msg=2)

    def test_annotate_raises_when_end_msg_is_not_none_nor_string(self):
        with pytest.raises(TypeError):
            annotate(end_msg=2)

    def test_annotate_does_not_modify_signature(self):
        expected_params = signature(self.func).parameters.keys()
        animated_func = annotate(start_msg='bogus')(self.func)
        actual_params = signature(self.func).parameters.keys()
        assert actual_params == expected_params

    def test_annotate_does_not_modify_doc(self):
        expected_doc = self.doc
        actual_doc = annotate(start_msg='herro')(self.func).__doc__
        assert actual_doc == expected_doc

    def test_annotate_prints_only_start_msg_and_newline_when_end_msg_is_none(
            self):
        with patch('sys.stdout', new=io.StringIO()) as mock_stdout:
            msg = 'This is the start'
            start_only = annotate(start_msg=msg)(self.func)
            start_only(1, 2, 3)  # 3 arbitrary arguments
            assert mock_stdout.getvalue() == msg + '\n'

    def test_annotate_ommits_newline_after_start_msg_if_no_start_nl(self):
        with patch('sys.stdout', new=io.StringIO()) as mock_stdout:
            msg = 'This is the start'
            start_only = annotate(start_msg=msg, start_no_nl=True)(self.func)
            start_only(1, 2, 3)  # 3 arbitrary arguments
            assert mock_stdout.getvalue() == msg

    def test_annotate_prints_only_end_msg_plus_newline_when_start_msg_is_none(
            self):
        with patch('sys.stdout', new=io.StringIO()) as mock_stdout:
            msg = 'This is the end'
            end_only = annotate(end_msg=msg)(self.func)
            end_only(1, 2, 3)  # 3 arbitrary arguments
            assert mock_stdout.getvalue() == msg + '\n'

    def test_annotate_prints_start_and_end_msgs_in_correct_order(self):
        with patch('sys.stdout', new=io.StringIO()) as mock_stdout:
            start_msg = 'This is the start'
            end_msg = 'This is the end'
            expected_print = start_msg + "\n" + end_msg + "\n"
            annotated = annotate(
                start_msg=start_msg, end_msg=end_msg)(self.func)
            annotated(1, 2, 3)
            assert mock_stdout.getvalue() == expected_print
