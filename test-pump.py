#!/usr/bin/env python3
"""Driver for stepper motors"""

import time
from RPi import GPIO
from driver import Pump

class GpioManager(object):

    def __enter__(self):
        GPIO.setmode(GPIO.BCM)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        GPIO.cleanup()
        return False


def test():
    with GpioManager() as _:
        pump = Pump(5)
        pump.on()
        time.sleep(1)
        pump.off()
        time.sleep(1)
        pump.drive(3)

if __name__ == "__main__":
    test()
