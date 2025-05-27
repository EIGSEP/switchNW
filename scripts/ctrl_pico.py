"""
This script gets copied to the pico and listens for commands from the Panda.
"""

import machine
import sys
import time

# set up the gpio switches
PINS = [2, 7, 1, 6, 3, 0, 4]
SETPINS = {
    f"idx{pindex}": machine.Pin(PINS[pindex], machine.Pin.OUT)
    for pindex in range(len(PINS))
}


def set_switch_states(statestr, pins=SETPINS):
    """
    Take a string of 0s and 1s from the controlling computer and set the
    GPIO pins to the corresponding states.

    Parameters
    ----------
    statestr : str
        A string of 0s and 1s representing the desired states of the pins.
        This may also include a trailing ! character to indicate verification.
    pins : dict
        A dictionary of pin objects keyed by their index.

    """
    verify = statestr.endswith("!")
    if verify:
        statestr = statestr[:-1]  # remove the trailing ! character
    states = [int(i) for i in statestr]  # processes the command
    if len(states) != len(pins):
        print("Not enough states for num of pins.")
        return

    for pindex, state in enumerate(states):
        if state not in (0, 1):
            print(f"invalid state value: {state}.")
            return

        # set the value of the pin at idx{pindex}
        pins[f"idx{pindex}"].value(state)

    if verify:
        reply = "".join(
            str(pins[f"idx{pindex}"].value()) for pindex in range(len(pins))
        )
        print(f"STATES:{reply}")


while True:
    command = sys.stdin.readline().strip()  # read a line from stdin
    if command:
        set_switch_states(statestr=command, pins=SETPINS)
    time.sleep(0.1)
