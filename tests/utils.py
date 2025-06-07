class DummyPin:
    """
    Mock up of a machine.Pin for testing.
    """

    def __init__(self, gpio):
        self.gpio = gpio
        self._value = 0

    def value(self, val=None):
        """
        Get or set the value of the pin.
        """
        if val is None:
            return self._value
        else:
            self._value = val
