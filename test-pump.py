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
        GPIO.setup(3, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(4, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(5, GPIO.OUT, initial=GPIO.LOW)
        GPIO.output(3, GPIO.HIGH)
        GPIO.output(4, GPIO.HIGH)
        GPIO.output(5, GPIO.HIGH)
        pump = Pump(17)
        pump.on()
        time.sleep(1)
        pump.off()
        time.sleep(1)
        pump.drive(3)
        GPIO.output(3, GPIO.LOW)
        GPIO.output(4, GPIO.LOW)
        GPIO.output(5, GPIO.LOW)

if __name__ == "__main__":
    test()
