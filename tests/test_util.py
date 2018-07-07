from unittest.mock import NonCallableMagicMock, MagicMock
from collections import namedtuple
import pytest
from clanimtk import util
from asynctest import CoroutineMock

SupervisorTestVariables = namedtuple(
    'SupervisorTestValues',
    ('async_function', 'sync_function', 'return_value', 'animation', 'step'))


@pytest.fixture()
def sup_fixt():
    """Supervisor fixture."""
    return_value = 42**42
    mock_animation = MagicMock()
    mock_sync_function = MagicMock(return_value=return_value)
    mock_async_function = CoroutineMock(return_value=return_value)
    step = .1
    return SupervisorTestVariables(
        async_function=mock_async_function,
        sync_function=mock_sync_function,
        animation=mock_animation,
        return_value=return_value,
        step=step)


def test_get_supervisor_with_async_function():
    async def async_func():
        pass

    supervisor = util.get_supervisor(async_func)
    assert util._async_supervisor == supervisor.func
    assert len(supervisor.args) == 1
    assert supervisor.args[0] == async_func


def test_get_supervisor_with_regular_function():
    func = lambda: None
    supervisor = util.get_supervisor(func)
    assert supervisor.func == util._sync_supervisor
    assert len(supervisor.args) == 1
    assert supervisor.args[0] == func


def test_get_supervisor_with_non_callable():
    mock_non_callable = NonCallableMagicMock()
    with pytest.raises(TypeError) as exc_info:
        util.get_supervisor(mock_non_callable)
    assert "not callable" in str(exc_info)
