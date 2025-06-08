import logging
import serial
import time

"""
The SwitchNetwork class sends commands to the pico connected to the serport.

Hard-coded variables:

PATHS dictionary. The keys start with where the path starts: either RF
(port connected to LNA) or VNA (port connected to the VNA), and end with the
end of the path - ANT (antenna), O, S, L (OSL standards), or N (noise source).

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


class SwitchNetwork:

    def __init__(
        self,
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
        paths : dict
            Dictionary mapping path names to their corresponding switch states.
        serport : str
            Serial port for Pico connection.
        timeout : float
            Timeout for each blocking call to the serial port.
        logger : logging.Logger
        redis : eigsep_observing.EigsepRedis
            Redis instance to push observing modes to.

        Raises
        ------
        ValueError
            If the serial port cannot be opened.

        """
        if logger is None:
            logger = logging.getLogger(__name__)
            logger.setLevel(logging.INFO)
        self.logger = logger
        self.paths = paths  # will just need to write this by hand
        self.redis = redis
        try:
            self.ser = serial.Serial(serport, 115200, timeout=timeout)
        except serial.SerialException as e:
            error_msg = f"Could not open serial port {serport}: {e}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)

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
            set_path = self._verify_switch()
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

    def _verify_switch(self):
        """
        Verify the current switch state by reading from the serial port.

        Returns
        -------
        set_path : str
            The current path set on the switch.

        Raises
        ------
        TimeoutError
            If no reply is received from the switch before timeout.

        ValueError
            If the reply from the switch does not start with "STATES".

        """
        reply = self.ser.readline().decode()
        if not reply:
            self.logger.error("No reply from the switch.")
            raise TimeoutError("No reply from the switch.")
        if not reply.startswith("STATES"):
            self.logger.error(f"Unexpected reply from switch: {reply}")
            raise ValueError(f"Unexpected reply from switch: {reply}")
        set_path = reply.rstrip("\n").split(":")[1]  # remove prefix
        set_path = set_path.strip()
        return set_path

    def powerdown(self, verify=False):
        """
        Switch to the low power state by setting all GPIOs to low.

        Parameters
        ----------
        verify : bool
            If True, will verify the switch state after setting it.

        Returns
        -------
        path : str
            The path that was set. Only returned if ``verify'' is True.

        """
        self.logger.info("Switching to low power mode.")
        out = self.switch(pathname=LOW_POWER_PATHNAME, verify=verify)

        if verify:
            path = out[0]
            return path
