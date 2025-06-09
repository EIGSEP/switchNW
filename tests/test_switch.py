import pytest

import switch_network
from switch_network import SwitchNetwork


@pytest.fixture
def dummy_switch():
    return switch_network.testing.DummySwitchNetwork()


def test_init_failure():
    with pytest.raises(ValueError):
        SwitchNetwork()  # can't open serial port


def test_switch(dummy_switch):
    assert dummy_switch is not None
    # switch paths
    for pathname in dummy_switch.paths:
        path = dummy_switch.paths[pathname]
        dummy_switch.switch(pathname, verify=False)
        nread = len(path) + 2
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
    dummy_switch.pico.write(b"0" * len(dummy_switch.setpins) + b"\n")
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
    assert path == "0" * len(dummy_switch.setpins)
