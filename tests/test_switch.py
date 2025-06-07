import logging
import pytest

from mockserial import create_serial_connection

import switch_network
from switch_network import SwitchNetwork
import utils


class DummySwitchNetwork(SwitchNetwork):
    """
    Mimic SwitchNetwork, but do not open a serial port.
    """

    def __init__(self):
        """
        Initialize the DummySwitchNetwork with a mock serial connection.

        """
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        self.logger = logger
        self.paths = switch_network.switch.PATHS
        self.gpios = switch_network.switch.GPIOS
        self.redis = None
        # create a dummy serial connection
        self.ser, self.pico = create_serial_connection(timeout=1)
        self._fail_switch = False  # simulate a failure in switching
        # create dummy setpins
        self.setpins = [utils.DummyPin(gpio) for gpio in self.gpios]

    def _do_switch_on_pico(self):
        """
        Simulate the pico switching.
        """
        nread = len(self.gpios) + 2
        command = self.pico.readline(nread).decode().strip()
        if command:
            if self._fail_switch:  # swap 0 and 1
                c1 = command.replace("0", "2")  # swap 0 with 2
                c2 = c1.replace("1", "0")  # swap 1 with 0
                command = c2.replace("2", "1")  # swap 2 with 1
            reply = switch_network.pico_utils.set_switch_states(
                command, self.setpins, return_states=True
            )
            if reply:
                self.pico.write(reply.encode())

    def _verify_switch(self):
        """
        Override verify method by mocking a Pico switching and
        responding. If the attribute _fail_switch is set to True,
        it will simulate a failure in switching.
        """
        # this part is in scripts/main.py and runs on the Pico
        self._do_switch_on_pico()
        # run the verify method
        return super()._verify_switch()

    def powerdown(self, verify=False):
        """
        Override powerdown method to simulate power down.
        """
        if verify:  # calls do_switch already
            return super().powerdown(verify=True)
        # run the powerdown method
        super().powerdown(verify=False)
        # this part is in scripts/main.py and runs on the Pico
        self._do_switch_on_pico()


@pytest.fixture
def dummy_switch():
    return DummySwitchNetwork()


def test_init_failure():
    with pytest.raises(ValueError):
        SwitchNetwork()  # can't open serial port


def test_switch(dummy_switch):
    assert dummy_switch is not None
    # switch paths
    for pathname in dummy_switch.paths:
        path = dummy_switch.paths[pathname]
        dummy_switch.switch(pathname, verify=False)
        nread = len(dummy_switch.gpios) + 2
        read = dummy_switch.pico.readline(nread).strip().decode()
        assert read == path
    # verify switch states
    for pathname in dummy_switch.paths:
        path = dummy_switch.paths[pathname]
        set_path, set_pathname, match = dummy_switch.switch(
            pathname, verify=True
        )
        assert match is True
        assert set_path == path
        assert switch_network.switch.PATHS[set_pathname] == set_path
    # failure in switching
    dummy_switch._fail_switch = True
    for pathname in dummy_switch.paths:
        path = dummy_switch.paths[pathname]
        set_path, set_pathname, match = dummy_switch.switch(
            pathname, verify=True
        )
        assert match is False
        assert set_path != path


def test_verify_switch(dummy_switch):
    for pathname in dummy_switch.paths:
        path = dummy_switch.paths[pathname]
        back = f"STATES:{path}\n"
        dummy_switch.pico.write(back.encode())
        set_path = SwitchNetwork._verify_switch(dummy_switch)
        assert set_path == path
    # send no path
    dummy_switch.pico.write(b"")
    with pytest.raises(TimeoutError):
        SwitchNetwork._verify_switch(dummy_switch)
    # send a path without STATES:
    dummy_switch.pico.write(b"0" * len(dummy_switch.gpios) + b"\n")
    with pytest.raises(ValueError):
        SwitchNetwork._verify_switch(dummy_switch)


def test_powerdown(dummy_switch):
    # set all pins to 1
    for pin in dummy_switch.setpins:
        pin.value(1)
    dummy_switch.powerdown(verify=False)  # should set all pins to 0
    for pin in dummy_switch.setpins:
        assert pin.value() == 0
    # with verify
    for pin in dummy_switch.setpins:
        pin.value(1)
    path = dummy_switch.powerdown(verify=True)
    assert path == "0" * len(dummy_switch.gpios)
