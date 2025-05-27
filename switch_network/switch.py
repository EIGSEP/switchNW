import logging
import numpy as np
import serial
import time

"""
The SwitchNetwork class sends commands to the pico connected to the serport.

Hard-coded variables:

PATHS dictionary. The keys start with where the path starts: either RF
(port connected to LNA) or VNA (port connected to the VNA), and end with the
end of the path - ANT (antenna), O, S, L (OSL standards), or N (noise source).

GPIOS list. gpio pin numbers - the index of the pin should correspond to the
index of the state it should be in for each path in PATHS.
"""
PATHS = {
    "VNAO": "1000000",
    "VNAS": "1100000",
    "VNAL": "0010000",
    "VNAANT": "0000010",
    "VNAN": "0000011",
    "VNARF": "0001100",
    "RFN": "0000001",
    "RFANT": "0000000",
}

GPIOS = [2, 7, 1, 6, 3, 0, 4]


class SwitchNetwork:

    def __init__(
        self,
        gpios=GPIOS,
        paths=PATHS,
        serport="/dev/ttyACM0",
        logger=None,
        redis=None,
    ):
        """
        Initialize the SwitchNetwork class.

        Parameters
        ----------
        gpios : list
            List of GPIO pins to be used for the switch network.
        paths : dict
            Dictionary mapping path names to their corresponding switch states.
        serport : str
            Serial port for Pico connection.
        logger : logging.Logger
        redis : eigsep_observing.EigsepRedis
            Redis instance to push observing modes to.

        """
        if logger is None:
            logger = logging.getLogger(__name__)
            logger.setLevel(logging.INFO)
        self.logger = logger
        self.paths = paths  # will just need to write this by hand.
        self.state = None  # state will initially be in the low power mode
        self.ser = serial.Serial(serport, 115200)
        self.gpios = gpios
        self.redis = redis
        self.powerdown()

    def switch(self, pathname):
        """
        Set switches at given GPIO pins to the low/high power modes specified
        by paths.

        Parameters
        ----------
        pathname : str
            The key for the path you want to switch to.

        """
        path = self.paths[pathname]
        self.ser.write(path.encode())  # encode the path and write to the Pico
        time.sleep(0.02)  # wait for switch
        pathsum = sum([int(i) for i in path])
        self.state = (pathname, pathsum)

        self.logger.info(f"{pathname} is set.")
        for idx, i in enumerate(self.gpios):
            self.logger.info(f"GPIO{i} set to {path[idx]}.")

        if self.redis is not None:
            self.redis.add_metadata("obs_mode", pathname)

    def powerdown(self):
        """
        Finds and switches to the lowest power mode in self.paths.

        """
        # call switch func on lowest power state.
        states = np.array(list(self.paths.keys()))
        pathstr = np.array(list(self.paths.values()))

        pathsums = np.array([sum([int(i) for i in path]) for path in pathstr])
        lowpower = states[pathsums == min(pathsums)][0]
        self.switch(pathname=lowpower)

        time.sleep(0.1)
