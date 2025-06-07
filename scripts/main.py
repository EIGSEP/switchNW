"""
This script gets copied to the pico and listens for commands from the Panda.
"""

import machine
import sys

from switch_network.pico_utils import set_switch_states

# set up the gpio switches
PINS = [4, 3, 1, 0, 2, 6, 7]
SETPINS = {
    f"idx{pindex}": machine.Pin(PINS[pindex], machine.Pin.OUT)
    for pindex in range(len(PINS))
}


while True:
    # read at most len(PINS) + verification character + newline
    command = sys.stdin.readline(len(PINS) + 2).strip()
    if command:
        set_switch_states(command, SETPINS)
