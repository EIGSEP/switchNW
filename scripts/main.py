"""
This script gets copied to the pico and listens for commands from the Panda.
"""

import machine
import sys

from switch_network.pico_utils import set_switch_states
from switch_network.switch import GPIOS

# set up the gpio switches
SETPINS = [machine.Pin(gpio, machine.Pin.OUT) for gpio in GPIOS]

while True:
    # read at most len(GPIOS) + verification character + newline
    command = sys.stdin.readline(len(GPIOS) + 2).strip()
    if command:
        set_switch_states(command, SETPINS)
