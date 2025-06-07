import logging
import pytest

from switch_network import SwitchNetwork


class DummySwitchNetwork(SwitchNetwork):
    """
    Mimic SwitchNetwork, but do not open a serial port.
    """
    def __init__(self, *args, **kwargs):
        kwargs["serport"] = None
        super().__init__(*args, **kwargs)

@pytest.fixture
def switch_network():
    return DummySwitchNetwork()

def test_init_failure():
    with pytest.raises(ValueError):
        SwitchNetwork()  # can't open serial port

def test_init(switch_network):
    assert switch_network is not None
    assert switch_network.ser is None  # dummy
    
