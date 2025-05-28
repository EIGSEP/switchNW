import logging
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
INV_PATHS = {v: k for k, v in PATHS.items()}
LOW_POWER_PATH = "0000000"  # all GPIOs low
LOW_POWER_PATHNAME = INV_PATHS[LOW_POWER_PATH]

GPIOS = [2, 7, 1, 6, 3, 0, 4]


class SwitchNetwork:

    def __init__(
        self,
        gpios=GPIOS,
        paths=PATHS,
        serport="/dev/ttyACM0",
        timeout=10,
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
        timeout : float
            Timeout for each blocking call to the serial port.
        logger : logging.Logger
        redis : eigsep_observing.EigsepRedis
            Redis instance to push observing modes to.

        """
        if logger is None:
            logger = logging.getLogger(__name__)
            logger.setLevel(logging.INFO)
        self.logger = logger
        self.paths = paths  # will just need to write this by hand.
        self.ser = serial.Serial(serport, 115200, timeout=timeout)
        self.gpios = gpios
        self.redis = redis
        self.powerdown()

    def switch(self, pathname, verify=True):
        """
        Set switches at given GPIO pins to the low/high power modes specified
        by paths. Returns the path that was set, its corresponding pathname,
        and if it matches the path requested if ``verify'' is True.

        Parameters
        ----------
        pathname : str
            The key for the path you want to switch to.
        verify : bool
            If True, will verify the switch state after setting it.

        Returns
        -------
        set_path : str
            The path that was set. Only returned if ``verify'' is True.
        set_pathname : str
            The pathname corresponding to the set path. Only returned if
            ``verify'' is True.
        match : bool
            If ``verify'' is True, returns whether the set path matches the
            requested path.

        """
        path = self.paths[pathname]
        if verify:
            path = path + "!"  # add a verification character
        # clear the serial buffer
        self.ser.reset_input_buffer()
        # encode the path and write to the Pico
        self.ser.write(path.encode() + b"\n")
        self.ser.flush()
        time.sleep(0.05)  # wait for switch
        self.logger.info(f"{pathname} is set.")
        if verify:
            while True:
                reply = self.ser.readline().decode()
                if not reply:
                    self.logger.error("No reply from the switch.")
                    raise TimeoutError("No reply from the switch.")
                if reply.startswith("STATES"):
                    break
            set_path = reply.rstrip("\n").split(":")[1]  # remove prefix
            match = set_path == path[:-1]  # remove the verification character
            if match:
                self.logger.info(f"Switch verified: {set_path}.")
                set_pathname = pathname
            else:
                self.logger.error(f"Switch verification failed: {set_path}.")
                set_pathname = INV_PATHS.get(set_path, "UNKNOWN")
            obs_mode = set_pathname
        else:
            obs_mode = pathname
        if self.redis is not None:
            self.redis.add_metadata("obs_mode", obs_mode)
        if verify:
            return set_path, set_pathname, match

    def powerdown(self, verify=False):
        """
        Switch to the low power state by setting all GPIOs to low.

        """
        self.logger.info("Switching to low power mode.")
        path = self.switch(pathname=LOW_POWER_PATHNAME, verify=verify)

        if verify:
            return path
