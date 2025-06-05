# Switch Network Control

[![codecov](https://codecov.io/gh/EIGSEP/switchNW/graph/badge.svg?token=9Z70IE4AQ8)](https://codecov.io/gh/EIGSEP/switchNW)

> This repository holds a package and scripts for controlling the switch network EIGSEP will use for automatic calibration.

**Installation**
```
> pip install <path/to/switchNW>
```

**Getting Started**
> There are two interfaces to work with here. One is the pi pico and one is the LattePanda sending the commands. 
> Both need to be hardcoded with the GPIO pin numbers, and the paths to each object.
> For a three-switch network, one would change the ctrl\_pico.py to use the right pin numbers in the list at the top. For example:
```
> pins = [0,1,2]
```
> Then, when initializing the SwitchNetwork Object, first set the correct paths to each object in a dictionary, the correct pins for the gpios argument, and the correct /dev/ttyACM* path for the USB serial.

**Resources**
> See EIGSEP memo in preparation. 

